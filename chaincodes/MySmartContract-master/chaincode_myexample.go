package main


import (
	"encoding/json"
	"fmt"
	"strconv"
	"time"

	"github.com/hyperledger/fabric/core/chaincode/shim"
	pb "github.com/hyperledger/fabric/protos/peer"
)

type SimpleChaincode struct {
}

type CenterBank struct {
	Name        string `json:"name"`        
	TotalNumber int    `json:"totalnumber"` 
	RestNumber  int    `json:"restnumber"`  
	ID          int    `json:"id"`          
}

type Bank struct {
	Name        string `json:"name"`        
	TotalNumber int    `json:"totalnumber"` 
	RestNumber  int    `json:"fromtype"`    
	ID          int    `json:"id"`          
}

type Company struct {
	Name   string `json:"name"`   
	Number int    `json:"number"` 
	ID     int    `json:"id"`     

}

type Transaction struct {
	FromType string `json:"fromtype"` 
	FromID   int    `json:"fromid"`   
	ToType   string `json:"totype"`   
	ToID     int    `json:"toid"`     
	Time     string `json:"time"`     
	Number   int    `json:"number"`   
	ID       int    `json:"id"`       
}

var center CenterBank

func (t *SimpleChaincode) Init(stub shim.ChaincodeStubInterface) pb.Response {
	fmt.Println("ex02 Init")
	_, args := stub.GetFunctionAndParameters()
	var centerBankName string  
	var TotalNumber_center int 
	var RestNumber_center int  
	var ID_center int          
	var err error
	if len(args) != 4 {
		return shim.Error("Incorrect number of arguments. Expecting 4")
	}

	centerBankName = args[0]

	TotalNumber_center, err = strconv.Atoi(args[1])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding TotalNumber_center")
	}
	RestNumber_center, err = strconv.Atoi(args[2])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding RestNumber_center")
	}
	ID_center, err = strconv.Atoi(args[3])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding ID_center")
	}

	fmt.Printf("centerBankName = %d, TotalNumber_center = %d, RestNumber_center=%d,ID_center=%d\n", centerBankName, TotalNumber_center, RestNumber_center, ID_center)

	center.Name = centerBankName
	center.TotalNumber = TotalNumber_center
	center.RestNumber = RestNumber_center
	center.ID = ID_center

	jsons, errs := json.Marshal(center) 

	if errs != nil {
		return shim.Error(errs.Error())
	}
	err = stub.PutState(args[3], jsons)
	if err != nil {
		return shim.Error(err.Error())
	}
	fmt.Printf(" init success \n")
	return shim.Success(nil)
}

func (t *SimpleChaincode) CreateBank(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 CreateBank")

	var Name string     
	var TotalNumber int 
	var RestNumber int  
	var ID int          

	var bank Bank
	var err error

	if len(args) != 4 {
		return shim.Error("Incorrect number of arguments. Expecting 4")
	}

	Name = args[0]

	TotalNumber, err = strconv.Atoi(args[1])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding TotalNumber ")
	}
	RestNumber, err = strconv.Atoi(args[2])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding RestNumber ")
	}
	ID, err = strconv.Atoi(args[3])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding ID ")
	}

	fmt.Printf(" Name = %d, TotalNumber  = %d, RestNumber =%d,ID =%d\n", Name, TotalNumber, RestNumber, ID)

	bank.Name = Name
	bank.TotalNumber = TotalNumber
	bank.RestNumber = RestNumber
	bank.ID = ID

	jsons, errs := json.Marshal(bank) 
	if errs != nil {
		return shim.Error(errs.Error())
	}

	err = stub.PutState(args[3], jsons)
	if err != nil {
		return shim.Error(err.Error())
	}
	fmt.Printf(" CeateBank success \n")
	return shim.Success(nil)
}

func (t *SimpleChaincode) CreateCompany(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 CreateCompany")

	var Name_company string 
	var Number int          
	var ID_company int      
	var err error
	var company Company

	if len(args) != 3 {
		return shim.Error("Incorrect number of arguments. Expecting 3")
	}

	Name_company = args[0]

	Number, err = strconv.Atoi(args[1])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding Number ")
	}
	ID_company, err = strconv.Atoi(args[2])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding ID_company ")
	}

	fmt.Printf(" Name_company = %d, Number  = %d,ID_company =%d\n", Name_company, Number, ID_company)

	company.Name = Name_company
	company.Number = Number
	company.ID = ID_company

	jsons, errs := json.Marshal(company) 
	if errs != nil {
		return shim.Error(errs.Error())
	}
	err = stub.PutState(args[2], jsons)
	if err != nil {
		return shim.Error(err.Error())
	}

	fmt.Printf("CreateCompany \n")

	return shim.Success(nil)
}

func (t *SimpleChaincode) IssueCoin(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 IssueCoin")

	var Number int        
	var ID_trans int      
	var trans Transaction 
	var err error
	if len(args) != 2 {
		return shim.Error("Incorrect number of arguments. Expecting 2")
	}


	Number, err = strconv.Atoi(args[0])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding Number ")
	}
	ID_trans, err = strconv.Atoi(args[1])

	if err != nil {
		return shim.Error("Expecting integer value for asset holding ID_trans ")
	}

	fmt.Printf("  Number  = %d ,ID_trans = %d \n", Number, ID_trans)

	trans.FromType = "0"
	trans.FromID = 0
	trans.ToType = "0"
	trans.ToID = 0

	cur_time := time.Now()
	trans.Time = cur_time.String()
	trans.Number = Number
	trans.ID = ID_trans

	center.RestNumber = center.RestNumber + Number

	jsons, errs := json.Marshal(trans) 
	if errs != nil {
		return shim.Error(errs.Error())
	}
	err = stub.PutState(args[1], jsons)
	if err != nil {
		return shim.Error(err.Error())
	}

	jsons_center, errs2 := json.Marshal(center) 
	if errs2 != nil {
		return shim.Error(errs2.Error())
	}
	err = stub.PutState("0", jsons_center)

	if err != nil {
		return shim.Error(err.Error())
	}
	fmt.Printf(" IssueCoin success \n")
	return shim.Success(nil)
}

func (t *SimpleChaincode) issueCoinToBank(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 IssueCoin")

	var Number int                
	var To_ID int                 
	var ID_trans int              
	var trans_to_bank Transaction 
	var toBank Bank               
	var err error
	if len(args) != 3 {
		return shim.Error("Incorrect number of arguments. Expecting 1")
	}


	Number, err = strconv.Atoi(args[1])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding Number ")
	}
	To_ID, err = strconv.Atoi(args[0])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding To_ID  ")
	}

	ID_trans, err = strconv.Atoi(args[2])

	if err != nil {
		return shim.Error("Expecting integer value for asset holding ID_trans ")
	}

	fmt.Printf("  Number  = %d ,To_ID =%d , ID_trans=%d\n", Number, To_ID, ID_trans)

	trans_to_bank.FromType = "0"
	trans_to_bank.FromID = 0
	trans_to_bank.ToType = "1"
	trans_to_bank.ToID = To_ID

	cur_time := time.Now()

	trans_to_bank.Time = cur_time.String()

	trans_to_bank.Number = Number
	trans_to_bank.ID = ID_trans

	center.RestNumber = center.RestNumber - Number

	toBankInfo, erro := stub.GetState(args[0])
	if erro != nil {
		return shim.Error(erro.Error())
	}

	err = json.Unmarshal(toBankInfo, &toBank)
	toBank.TotalNumber = Number
	toBank.RestNumber = toBank.RestNumber + Number

	fmt.Printf("  toBankInfo  = %d  \n", toBankInfo)

	jsons, errs := json.Marshal(trans_to_bank) 
	if errs != nil {
		return shim.Error(errs.Error())
	}
	ID_trans_string := strconv.Itoa(ID_trans)
	err = stub.PutState(ID_trans_string, jsons)
	if err != nil {
		return shim.Error(err.Error())
	}

	jsons_toBank, errs2 := json.Marshal(toBank) 
	if errs2 != nil {
		return shim.Error(errs2.Error())
	}
	toBankID_string := strconv.Itoa(toBank.ID)
	err = stub.PutState(toBankID_string, jsons_toBank)
	if err != nil {
		return shim.Error(err.Error())
	}

	jsons_center, errs3 := json.Marshal(center) 
	if errs3 != nil {
		return shim.Error(errs3.Error())
	}
	centerID_string := strconv.Itoa(center.ID)
	err = stub.PutState(centerID_string, jsons_center)
	if err != nil {
		return shim.Error(err.Error())
	}

	fmt.Printf("  issueCoinToBank success \n")
	return shim.Success(nil)
}

func (t *SimpleChaincode) issueCoinToCp(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 IssueCoin")

	var Number int             
	var From_ID int            
	var To_ID int              
	var ID int                 
	var bank_to_cp Transaction 
	var bankFrom Bank          
	var cpTo Company           
	var err error
	if len(args) != 4 {
		return shim.Error("Incorrect number of arguments. Expecting 4")
	}


	From_ID, err = strconv.Atoi(args[0])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding From_ID ")
	}
	Number, err = strconv.Atoi(args[2])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding Number ")
	}
	To_ID, err = strconv.Atoi(args[1])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding To_ID  ")
	}

	ID, err = strconv.Atoi(args[3])

	if err != nil {
		return shim.Error("Expecting integer value for asset holding ID_trans ")
	}

	fmt.Printf("  Number  = %d ,To_ID =%d , ID_trans=%d\n", Number, To_ID, ID)

	bank_to_cp.FromType = "1"
	bank_to_cp.FromID = From_ID
	bank_to_cp.ToType = "2"
	bank_to_cp.ToID = To_ID

	cur_time := time.Now()
	bank_to_cp.Time = cur_time.String()

	bank_to_cp.Number = Number
	bank_to_cp.ID = ID

	BankFromBytes, erro := stub.GetState(args[0])
	if erro != nil {
		return shim.Error(erro.Error())
	}

	err = json.Unmarshal(BankFromBytes, &bankFrom)
	bankFrom.RestNumber = bankFrom.RestNumber - Number

	jsons_bank, errs := json.Marshal(bankFrom) 
	if errs != nil {
		return shim.Error(errs.Error())
	}
	bankFromID_string := strconv.Itoa(bankFrom.ID)

	err = stub.PutState(bankFromID_string, jsons_bank)

	companyToBytes, erro1 := stub.GetState(args[1])
	if erro1 != nil {
		return shim.Error(erro1.Error())
	}
	err = json.Unmarshal(companyToBytes, &cpTo)
	cpTo.Number = cpTo.Number + Number

	jsons_cp, errs2 := json.Marshal(cpTo) 
	if errs2 != nil {
		return shim.Error(errs2.Error())
	}
	cpToID_string := strconv.Itoa(cpTo.ID)
	err = stub.PutState(cpToID_string, jsons_cp)

	jsons, errs3 := json.Marshal(bank_to_cp) 
	if errs3 != nil {
		return shim.Error(errs3.Error())
	}
	ID_string := strconv.Itoa(ID)
	err = stub.PutState(ID_string, jsons)
	if err != nil {
		return shim.Error(err.Error())
	}

	return shim.Success(nil)
}

func (t *SimpleChaincode) getBanks(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 getBanks")

	var Bank_ID string 
	var bank_info Bank
	var err error
	if len(args) != 1 {
		return shim.Error("Incorrect number of arguments. Expecting 1")
	}


	Bank_ID = args[0]

	BankInfo, erro := stub.GetState(Bank_ID)
	if erro != nil {
		return shim.Error(erro.Error())
	}
	err = json.Unmarshal(BankInfo, &bank_info)
	if err != nil {
		return shim.Error(err.Error())
	}
	fmt.Printf("  BankInfo  = %d  \n", BankInfo)

	return shim.Success(nil)
}

func (t *SimpleChaincode) getCompanys(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 getCompanys")

	var CP_ID string 
	var company_info Company
	var err error
	if len(args) != 1 {
		return shim.Error("Incorrect number of arguments. Expecting 1")
	}


	CP_ID = args[0]

	company_info_bytes, erro := stub.GetState(CP_ID)
	if erro != nil {
		return shim.Error(erro.Error())
	}


	err = json.Unmarshal(company_info_bytes, &company_info)
	if err != nil {
		return shim.Error(err.Error())
	}

	fmt.Printf("  BankInfo  = %d  \n", company_info_bytes)

	return shim.Success(nil)
}

func (t *SimpleChaincode) getTransactions(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 getCompanys")

	var trans_ID string 
	var trans_info Transaction
	var err error
	if len(args) != 1 {
		return shim.Error("Incorrect number of arguments. Expecting 1")
	}


	trans_ID = args[0]

	trans_info_bytes, erro := stub.GetState(trans_ID)
	if erro != nil {
		return shim.Error(erro.Error())
	}


	err = json.Unmarshal(trans_info_bytes, &trans_info)
	if err != nil {
		return shim.Error(err.Error())
	}
	fmt.Printf("  trans_info_bytes  = %d  \n", trans_info_bytes)

	return shim.Success(nil)
}

func (t *SimpleChaincode) getCenterBank(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 getCenterBank")

	var Center_ID string 
	var center_info CenterBank
	var err error
	if len(args) != 1 {
		return shim.Error("Incorrect number of arguments. Expecting 1")
	}


	Center_ID = args[0]

	center_info_bytes, erro := stub.GetState(Center_ID)
	if erro != nil {
		return shim.Error(erro.Error())
	}


	err = json.Unmarshal(center_info_bytes, &center_info)
	if err != nil {
		return shim.Error(err.Error())
	}
	fmt.Printf("  center_info_bytes  = %d  \n", center_info_bytes)

	return shim.Success(nil)
}

func (t *SimpleChaincode) transfer(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	fmt.Println("ex02 getCenterBank")

	var From_ID int 
	var To_ID int   
	var number int  
	var fromCP Company
	var toCP Company
	var err error

	if len(args) != 3 {
		return shim.Error("Incorrect number of arguments. Expecting 3")
	}


	From_ID, err = strconv.Atoi(args[0])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding From_ID  ")
	}
	To_ID, err = strconv.Atoi(args[1])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding To_ID  ")
	}
	number, err = strconv.Atoi(args[2])
	if err != nil {
		return shim.Error("Expecting integer value for asset holding number ")
	}

	fromID_string := strconv.Itoa(From_ID)
	from_cp_info_bytes, erro := stub.GetState(fromID_string)
	if erro != nil {
		return shim.Error(erro.Error())
	}


	err = json.Unmarshal(from_cp_info_bytes, &fromCP)

	fmt.Printf("  from_cp_info_bytes  = %d  \n", from_cp_info_bytes)

	To_ID_string := strconv.Itoa(To_ID)
	to_cp_info_bytes, erro1 := stub.GetState(To_ID_string)
	if erro1 != nil {
		return shim.Error(erro1.Error())
	}


	err = json.Unmarshal(to_cp_info_bytes, &toCP)

	fmt.Printf("  to_cp_info_bytes  = %d  \n", to_cp_info_bytes)

	from_cp_old_num := fromCP.Number
	if from_cp_old_num <= number {
		return shim.Error("money no enough")
	}

	fromCP.Number = from_cp_old_num - number

	to_cp_old_num := toCP.Number
	toCP.Number = to_cp_old_num + number

	jsons_from, errs := json.Marshal(fromCP) 
	if errs != nil {
		return shim.Error(errs.Error())
	}
	fromCPID_string := strconv.Itoa(fromCP.ID)
	err = stub.PutState(fromCPID_string, jsons_from)
	if err != nil {
		return shim.Error(err.Error())
	}

	jsons_to, errs2 := json.Marshal(toCP) 
	if errs2 != nil {
		return shim.Error(errs2.Error())
	}
	toCPID_string := strconv.Itoa(toCP.ID)
	err = stub.PutState(toCPID_string, jsons_to)
	if err != nil {
		return shim.Error(err.Error())
	}
	fmt.Printf(" transfer success \n")
	return shim.Success(nil)
}

func (t *SimpleChaincode) delete(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	if len(args) != 1 {
		return shim.Error("Incorrect number of arguments. Expecting 1")
	}

	A := args[0]

	err := stub.DelState(A)
	if err != nil {
		return shim.Error("Failed to delete state")
	}

	return shim.Success(nil)
}
func (t *SimpleChaincode) Invoke(stub shim.ChaincodeStubInterface) pb.Response {
	fmt.Println("ex02 Invoke")
	function, args := stub.GetFunctionAndParameters()
	if function == "invoke" {
		return t.invoke(stub, args)
	} else if function == "delete" {
		return t.delete(stub, args)
	} else if function == "query" {
		return t.query(stub, args)
	} else if function == "CreateBank" {
		return t.CreateBank(stub, args)
	} else if function == "CreateCompany" {
		return t.CreateCompany(stub, args)
	} else if function == "getBanks" {
		return t.getBanks(stub, args)
	} else if function == "getCenterBank" {
		return t.getCenterBank(stub, args)
	} else if function == "getCompanys" {
		return t.getCompanys(stub, args)
	} else if function == "getTransactions" {
		return t.getTransactions(stub, args)
	} else if function == "IssueCoin" {
		return t.IssueCoin(stub, args)
	} else if function == "issueCoinToBank" {
		return t.issueCoinToBank(stub, args)
	} else if function == "issueCoinToCp" {
		return t.issueCoinToCp(stub, args)
	} else if function == "transfer" {
		return t.transfer(stub, args)
	}

	return shim.Error("Invalid invoke function name. Expecting \"invoke\" \"delete\" \"query\"")
}

func (t *SimpleChaincode) invoke(stub shim.ChaincodeStubInterface, args []string) pb.Response {

	return shim.Success(nil)
}


func (t *SimpleChaincode) query(stub shim.ChaincodeStubInterface, args []string) pb.Response {
	var A string 
	var err error

	if len(args) != 1 {
		return shim.Error("Incorrect number of arguments. Expecting name of the person to query")
	}

	A = args[0]

	Avalbytes, erro := stub.GetState(A)
	if erro != nil {
		return shim.Error(erro.Error())
	}
	if err != nil {
		jsonResp := "{\"Error\":\"Failed to get state for " + A + "\"}"
		return shim.Error(jsonResp)
	}

	if Avalbytes == nil {
		jsonResp := "{\"Error\":\"Nil amount for " + A + "\"}"
		return shim.Error(jsonResp)
	}

	jsonResp := "{\"Name\":\"" + A + "\",\"Amount\":\"" + string(Avalbytes) + "\"}"
	fmt.Printf("Query Response:%s\n", jsonResp)
	return shim.Success(Avalbytes)
}

func main() {
	err := shim.Start(new(SimpleChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}
