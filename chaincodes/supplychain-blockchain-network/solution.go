package main

import (
	"encoding/json"
	"fmt"
	"strconv"

	"github.com/hyperledger/fabric/core/chaincode/shim"
	pb "github.com/hyperledger/fabric/protos/peer"
)

type LogisticsChaincode struct {
}

type Seller struct {
	Id       string
	Name     string
	Location string
}

type Buyer struct {
	Id       string
	Name     string
	Location string
}

type LogisticsProvider struct {
	Id       string
	Name     string
	Location string
}

type Shipment struct {
	Id                  string
	Content             string
	WeightInKgs         int 
	SellerId            string
	LogisticsProviderId string
	BuyerId             string
	TemperatureReadings map[string]float64
	Status              string
}

var buyerStore map[string]Buyer
var sellerStore map[string]Seller
var logisticsProviderStore map[string]LogisticsProvider
var shipmentStore map[string]Shipment

func (t *LogisticsChaincode) Init(stub shim.ChaincodeStubInterface) pb.Response {
	fmt.Println("Initiated the chaincode")
	_, args := stub.GetFunctionAndParameters()

	if len(args) != 0 {
		return shim.Error("Incorrect number of arguments. Expecting 4")
	}

	return shim.Success(nil)
}

func (t *LogisticsChaincode) Invoke(stub shim.ChaincodeStubInterface) pb.Response {
	function, _ := stub.GetFunctionAndParameters()

	fmt.Println("The function invoked is ", function)
	if function == "registerSeller" {
		return t.registerSeller(stub)
	} else if function == "registerLogisticsProvider" {
		return t.registerLogisticsProvider(stub)
	} else if function == "registerBuyer" {
		return t.registerBuyer(stub)
	} else if function == "getSeller" {
		return t.getSeller(stub)
	} else if function == "getBuyer" {
		return t.getBuyer(stub)
	} else if function == "getLogisticsProvider" {
		return t.getLogisticsProvider(stub)
	} else if function == "registerShipment" {
		return t.registerShipment(stub)
	} else if function == "getShipments" {
		return t.getShipments(stub)
	} else if function == "updateShipmentTemperature" {
		return t.updateShipmentTemperature(stub)
	} else if function == "updateShipmentStatus" {
		return t.updateShipmentStatus(stub)
	} else {
		return shim.Success(nil)
	}
}

func main() {
	err := shim.Start(new(LogisticsChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}

func (t *LogisticsChaincode) registerSeller(stub shim.ChaincodeStubInterface) pb.Response {
	fmt.Println("In the buyer seller function")

	_, args := stub.GetFunctionAndParameters()

	if len(args) != 3 {
		return shim.Error("registerSeller function expects exactly 3 arguments")
	}

	sellerId := args[0]
	sellerName := args[1]
	sellerLocation := args[2]

	sellerStore := make(map[string]Seller)
	sellerStore["seller01"] = Seller{sellerId, sellerName, sellerLocation}

	fmt.Println(sellerStore)
	bytearray, _ := json.Marshal(sellerStore)

	fmt.Println(string(bytearray))

	err := stub.PutState("sellerstore", bytearray)
	if err != nil {
		fmt.Println("While writing sellerstore to ledger, error encountered ", err)
		return shim.Error("Error occurrered while writing sellerstore to the ledger")
	}

	return shim.Success([]byte("Successfully written sellerstore to the ledger"))
}

func (t *LogisticsChaincode) registerBuyer(stub shim.ChaincodeStubInterface) pb.Response {
	fmt.Println("In the buyer buyer function")

	_, args := stub.GetFunctionAndParameters()

	if len(args) != 3 {
		return shim.Error("registerBuyer function expects exactly 3 arguments")
	}

	buyerId := args[0]
	buyerName := args[1]
	buyerLocation := args[2]

	buyerStore := make(map[string]Buyer)
	buyerStore["buyer01"] = Buyer{buyerId, buyerName, buyerLocation}

	fmt.Println(buyerStore)
	bytearray, _ := json.Marshal(buyerStore)

	fmt.Println(string(bytearray))

	err := stub.PutState("buyerstore", bytearray)
	if err != nil {
		fmt.Println("While writing buyerstore to ledger, error encountered ", err)
		return shim.Error("Error occurrered while writing buyerstore to the ledger")
	}

	return shim.Success([]byte("Successfully written buyerstore to the ledger"))

}

func (t *LogisticsChaincode) registerLogisticsProvider(stub shim.ChaincodeStubInterface) pb.Response {
	fmt.Println("In the buyer logistics provider function")

	_, args := stub.GetFunctionAndParameters()

	if len(args) != 3 {
		return shim.Error("registerLogisticsProvider function expects exactly 3 arguments")
	}

	logisticsProviderId := args[0]
	logisticsProviderName := args[1]
	logisticsProviderLocation := args[2]

	logisticsProviderStore := make(map[string]LogisticsProvider)
	logisticsProviderStore["transporter01"] = LogisticsProvider{logisticsProviderId, logisticsProviderName, logisticsProviderLocation}

	fmt.Println(logisticsProviderStore)
	bytearray, _ := json.Marshal(logisticsProviderStore)

	fmt.Println(string(bytearray))

	err := stub.PutState("logisticsproviderstore", bytearray)
	if err != nil {
		fmt.Println("While writing logisticsProviderstore to ledger, error encountered ", err)
		return shim.Error("Error occurrered while writing logisticsProviderstore to the ledger")
	}

	return shim.Success([]byte("Successfully written logisticsProviderstore to the ledger"))
}

func (t *LogisticsChaincode) getSeller(stub shim.ChaincodeStubInterface) pb.Response {
	_, parameters := stub.GetFunctionAndParameters()

	var sellerId = parameters[0]

	sellerbytes, err := stub.GetState("sellerstore")
	if err != nil {
		return shim.Error("Could not retrieve seller store from the ledger")
	}

	sellerStore = make(map[string]Seller)

	err = json.Unmarshal(sellerbytes, &sellerStore)
	if err != nil {
		fmt.Println(string(sellerbytes))
		fmt.Println(err)
		return shim.Error("Error while unmarshaling data retrieved from the ledger")
	}

	fmt.Println(sellerStore[sellerId].Name)
	return shim.Success([]byte("Successfully retrieved the json data from the ledger"))

}

func (t *LogisticsChaincode) getBuyer(stub shim.ChaincodeStubInterface) pb.Response {
	_, parameters := stub.GetFunctionAndParameters()

	var buyerId = parameters[0]

	buyerbytes, err := stub.GetState("buyerstore")
	if err != nil {
		return shim.Error("Could not retrieve buyer store from the ledger")
	}

	buyerStore = make(map[string]Buyer)

	err = json.Unmarshal(buyerbytes, &buyerStore)
	if err != nil {
		fmt.Println(string(buyerbytes))
		fmt.Println(err)
		return shim.Error("Error while unmarshaling data retrieved from the ledger")
	}

	fmt.Println(buyerStore[buyerId].Name)
	return shim.Success([]byte("Successfully retrieved the json data from the ledger"))

}

func (t *LogisticsChaincode) getLogisticsProvider(stub shim.ChaincodeStubInterface) pb.Response {
	_, parameters := stub.GetFunctionAndParameters()

	var logisticsProviderId = parameters[0]

	logisticsproviderbytes, err := stub.GetState("logisticsproviderstore")
	if err != nil {
		return shim.Error("Could not retrieve logistics provider store from the ledger")
	}

	logisticsProviderStore = make(map[string]LogisticsProvider)

	err = json.Unmarshal(logisticsproviderbytes, &logisticsProviderStore)
	if err != nil {
		fmt.Println(string(logisticsproviderbytes))
		fmt.Println(err)
		return shim.Error("Error while unmarshaling data retrieved from the ledger")
	}

	fmt.Println(logisticsProviderStore[logisticsProviderId].Name)
	return shim.Success([]byte("Successfully retrieved the json data from the ledger"))
}

func (t *LogisticsChaincode) registerShipment(stub shim.ChaincodeStubInterface) pb.Response {


	_, parameters := stub.GetFunctionAndParameters()

	if len(parameters) != 6 {
		return shim.Error("Exactly 6 parameters are expected by the function: registerShipment")
	}

	fmt.Println(parameters)
	shipmentId := parameters[0]
	shipmentContent := parameters[1]
	shipmentWeightInKgs, errex := strconv.Atoi(parameters[2]) 
	if errex != nil {
		return shim.Error("Can't convert string weightinkgs to int weightinkigs")
	}
	shipmentSeller := parameters[3]
	shipmentLogisticsProvider := parameters[4]
	shipmentBuyer := parameters[5]


	shipment := Shipment{shipmentId, shipmentContent, shipmentWeightInKgs, shipmentSeller, shipmentLogisticsProvider, shipmentBuyer, make(map[string]float64), "In-Store"}
	fmt.Println(shipment)
	shipmentbytes, err := stub.GetState("shipmentstore")

	if err != nil {
		return shim.Error("Error retrieving the shipmentstore from the ledger")
	}

	shipmentStore = make(map[string]Shipment)

	if len(shipmentbytes) != 0 {
		fmt.Println("The shipmentstore in ledger is not empty")
		err = json.Unmarshal(shipmentbytes, &shipmentStore)
		if err != nil {
			return shim.Error("Can't unmarshal the shipmentbytes to structure")
		}
	}

	shipmentStore[shipmentId] = shipment

	shipmentbytes, err = json.Marshal(shipmentStore)

	if err != nil {
		fmt.Println("Error marshaling the shipmentStore to json string")
		return shim.Error("Error marshaling the shipmentStore to json string")
	}
	err = stub.PutState("shipmentstore", shipmentbytes)
	if err != nil {
		fmt.Println("Can't write shipmentbytes to the ledger")
		return shim.Error("Can't write shipmentbytes to the ledger")
	}

	return shim.Success([]byte("Successfully registered the shipment with the ledger"))
}

func (t *LogisticsChaincode) getShipments(stub shim.ChaincodeStubInterface) pb.Response {

	_, args := stub.GetFunctionAndParameters()

	actorType := args[0]
	actorId := args[1]


	returnShipment := make(map[string]Shipment)

	shipmentbytes, err := stub.GetState("shipmentstore")

	if err != nil {
		return shim.Error("Can't retrieve the shipment store from the ledger")
	}

	if len(shipmentbytes) == 0 {
		return shim.Success([]byte("Shipment store is empty"))
	}

	shipmentStore = make(map[string]Shipment)

	err = json.Unmarshal(shipmentbytes, &shipmentStore)
	if err != nil {
		return shim.Error("Error unmarshaling the shipmentstore bytes to structure")
	}

	fmt.Println("Reached here")

	fmt.Println(string(shipmentbytes))

	if actorType == "seller" {

		for id, shipment := range shipmentStore {
			if shipment.SellerId == actorId {
				returnShipment[id] = shipment
			}
		}

	} else if actorType == "buyer" {

		for id, shipment := range shipmentStore {
			if shipment.BuyerId == actorId {
				returnShipment[id] = shipment
			}
		}

	} else {

		for id, shipment := range shipmentStore {
			if shipment.LogisticsProviderId == actorId {
				returnShipment[id] = shipment
			}
		}

	}

	shipmentbytes, err = json.Marshal(returnShipment)
	if err != nil {
		return shim.Error("Can't marshal the returnShipment object to json string")
	}

	return shim.Success(shipmentbytes)
}

func (t *LogisticsChaincode) updateShipmentTemperature(stub shim.ChaincodeStubInterface) pb.Response {


	_, args := stub.GetFunctionAndParameters()

	if len(args) != 4 {
		return shim.Error("updateShipmentTemperature function requires exactly 4 arguments")
	}
	shipmentId := args[1]
	time := args[2]
	temperature, err := strconv.ParseFloat(args[3], 64)

	if err != nil {
		return shim.Error("Error converting the temperatre reading from string to float64")
	}

	shipment := Shipment{}
	shipment.TemperatureReadings = make(map[string]float64)

	shipmentbytes, err := stub.GetState("shipmentstore")

	shipmentStore := make(map[string]Shipment)

	err = json.Unmarshal(shipmentbytes, &shipmentStore)

	valueSet := false

	fmt.Println(shipmentStore)

	for id, shipmentValue := range shipmentStore {
		if id == shipmentId {
			shipment = shipmentValue
			valueSet = true
			break
		}
	}

	if valueSet == false {
		return shim.Error("Can't find the request shipment")
	}

	shipment.TemperatureReadings = make(map[string]float64)
	shipment.TemperatureReadings[time] = temperature

	shipmentStore[shipmentId] = shipment

	shipmentbytes, err = json.Marshal(shipmentStore)

	if err != nil {
		return shim.Error("Can't convert shipmentStore to json string bytes")
	}

	err = stub.PutState("shipmentstore", shipmentbytes)
	if err != nil {
		return shim.Error("Error updating the shipmentStore in the ledger")
	}

	return shim.Success([]byte("Successfully updated the temperature of the shipment in the ledger"))
}

func (t *LogisticsChaincode) updateShipmentStatus(stub shim.ChaincodeStubInterface) pb.Response {
	_, args := stub.GetFunctionAndParameters()

	if len(args) != 4 {
		return shim.Error("The function updateShipmentStatus requires exactly 4 arguments: actorType, actorId, shipmentId, newStatus ")
	}

	shipmentId := args[2]
	newStatus := args[3]


	shipmentbytes, err := stub.GetState("shipmentstore")
	if err != nil {
		return shim.Error("Can't retrieve the shipmentstore from the ledger")
	}

	if len(shipmentbytes) == 0 {
		return shim.Error("Can't update the required shipment status, because the shipment store is empty, there are no shipments registered")
	}

	shipmentStore := make(map[string]Shipment)

	err = json.Unmarshal(shipmentbytes, &shipmentStore)
	if err != nil {
		return shim.Error("Can't convert shipmentstore from []byte to golang structure")
	}

	shipment := Shipment{}
	shipment.TemperatureReadings = make(map[string]float64)
	valueSet := false
	for id, shipmentValue := range shipmentStore {
		if id == shipmentId {
			shipment = shipmentValue
			valueSet = true
			break
		}
	}

	if valueSet == false {
		return shim.Error("Can't update the status of the shipment, as the required shipment does not exist")
	}

	shipment.Status = newStatus
	shipmentStore[shipmentId] = shipment


	shipmentbytes, err = json.Marshal(shipmentStore)
	if err != nil {
		return shim.Error("Error converting shipmentStore from golang structure to json string []byte")
	}

	err = stub.PutState("shipmentstore", shipmentbytes)
	if err != nil {
		return shim.Error("Error storing the shipmentstore in the ledger")
	}

	fmt.Println("Successfully updated the shipment ", shipment, "with the new status value ", newStatus)

	return shim.Success([]byte("Successfully updated the requested shipment status with the provided status value"))
}