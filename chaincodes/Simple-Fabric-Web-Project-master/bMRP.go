package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric/core/chaincode/shim"
	pb "github.com/hyperledger/fabric/protos/peer"
)

type bMRPChainCode struct {
}

type Patient struct {
	PatientName        string `json:PatientName`
	PatientGender      int    `json:PatientGender`
	PatientAge         string `json:PatientAge`
	PatientNationality string `json:PatientNationality`
	PatientIDType      string `json:PatientIDType`
	PatientIDNumber    string `json:PatientIDNumber`
	PatientTelephone   string `json:PatientTelephone`
	PatientAddress     string `json:PatientAddress`
}

type Doctor struct {
	DoctorName         string `json:DoctorName`
	DoctorID           string `json:DoctorID`
	DoctorHospitalName string `json:DoctorHospitalName`
	DoctorHosptialID   string `json:DoctorHosptialID`
}

type MedicalRecord struct {
	MRID            string `json:MRID`
	MRAdmissionDate string `json:MRAdmissionDate`
	MRDischargeDate string `json:MRDischargeDate`
	MRPaymentType   string `json:MRPaymentType`
	MRPatientID     string `json:MRPatientID`
	MRDoctors       string `json:MRDoctors`
	MRDiagnosis     string `json:MRDiagnosis`
}

func (a *bMRPChainCode) Init(stub shim.ChaincodeStubInterface) pb.Response {
	return shim.Success(nil)
}

func (a *bMRPChainCode) Invoke(stub shim.ChaincodeStubInterface) pb.Response {
	fn, args := stub.GetFunctionAndParameters()
	if fn == "AddNewMR" {
		return a.AddNewMR(stub, args)
	} else if fn == "GetMRByID" {
		return a.GetMRByID(stub, args)
	}

	return shim.Error("Recevied unkown function invocation : " + fn)
}

func (a *bMRPChainCode) AddNewMR(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	var err error
	var newRecord MedicalRecord
	if len(args) != 7 {
		return shim.Error("Incorrect number of arguments.")
	}
	newRecord.MRID = args[0]
	newRecord.MRAdmissionDate = args[1]
	newRecord.MRDischargeDate = args[2]
	newRecord.MRPaymentType = args[3]
	newRecord.MRPatientID = args[4]
	newRecord.MRDoctors = args[5]
	newRecord.MRDiagnosis = args[6]

	ProInfosJSONasBytes, err := json.Marshal(newRecord)
	if err != nil {
		return shim.Error(err.Error())
	}

	err = stub.PutState(newRecord.MRID, ProInfosJSONasBytes)
	if err != nil {
		return shim.Error(err.Error())
	}
	return shim.Success(nil)
}

func (a *bMRPChainCode) GetMRByID(stub shim.ChaincodeStubInterface, args []string) pb.Response {

	if len(args) != 1 {
		return shim.Error("Incorrect number of arguments.")
	}
	MRID := args[0]
	resultsIterator, err := stub.GetHistoryForKey(MRID)
	if err != nil {
		return shim.Error(err.Error())
	}
	defer resultsIterator.Close()

	var medicalRecord MedicalRecord

	for resultsIterator.HasNext() {
		var _medicalRecord MedicalRecord
		response, err := resultsIterator.Next()
		if err != nil {
			return shim.Error(err.Error())
		}
		json.Unmarshal(response.Value, &_medicalRecord)
		if _medicalRecord.MRID != "" {
			medicalRecord = _medicalRecord
			continue
		}
	}
	jsonsAsBytes, err := json.Marshal(medicalRecord)
	if err != nil {
		return shim.Error(err.Error())
	}
	return shim.Success(jsonsAsBytes)
}

func main() {
	err := shim.Start(new(bMRPChainCode))
	if err != nil {
		fmt.Printf("Error starting bMRP chaincode: %s ", err)
	}
}
