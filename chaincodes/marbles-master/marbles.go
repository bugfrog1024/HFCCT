
package main

import (
	"fmt"
	"strconv"

	"github.com/hyperledger/fabric/core/chaincode/shim"
	pb "github.com/hyperledger/fabric/protos/peer"
)

type SimpleChaincode struct {
}


type Marble struct {
	ObjectType string        `json:"docType"` 
	Id       string          `json:"id"`      
	Color      string        `json:"color"`
	Size       int           `json:"size"`    
	Owner      OwnerRelation `json:"owner"`
}

type Owner struct {
	ObjectType string `json:"docType"`     
	Id         string `json:"id"`
	Username   string `json:"username"`
	Company    string `json:"company"`
	Enabled    bool   `json:"enabled"`     
}

type OwnerRelation struct {
	Id         string `json:"id"`
	Username   string `json:"username"`    
	Company    string `json:"company"`     
}

func main() {
	err := shim.Start(new(SimpleChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode - %s", err)
	}
}


func (t *SimpleChaincode) Init(stub shim.ChaincodeStubInterface) pb.Response {
	fmt.Println("Marbles Is Starting Up")
	funcName, args := stub.GetFunctionAndParameters()
	var number int
	var err error
	txId := stub.GetTxID()
	
	fmt.Println("Init() is running")
	fmt.Println("Transaction ID:", txId)
	fmt.Println("  GetFunctionAndParameters() function:", funcName)
	fmt.Println("  GetFunctionAndParameters() args count:", len(args))
	fmt.Println("  GetFunctionAndParameters() args found:", args)

	if len(args) == 1 {
		fmt.Println("  GetFunctionAndParameters() arg[0] length", len(args[0]))

		if len(args[0]) == 0 {
			fmt.Println("  Uh oh, args[0] is empty...")
		} else {
			fmt.Println("  Great news everyone, args[0] is not empty")

			number, err = strconv.Atoi(args[0])
			if err != nil {
				return shim.Error("Expecting a numeric string argument to Init() for instantiate")
			}

			err = stub.PutState("selftest", []byte(strconv.Itoa(number)))
			if err != nil {
				return shim.Error(err.Error())                  
			}
		}
	}

	alt := stub.GetStringArgs()
	fmt.Println("  GetStringArgs() args count:", len(alt))
	fmt.Println("  GetStringArgs() args found:", alt)

	err = stub.PutState("marbles_ui", []byte("4.0.1"))
	if err != nil {
		return shim.Error(err.Error())
	}

	fmt.Println("Ready for action")                          
	return shim.Success(nil)
}


func (t *SimpleChaincode) Invoke(stub shim.ChaincodeStubInterface) pb.Response {
	function, args := stub.GetFunctionAndParameters()
	fmt.Println(" ")
	fmt.Println("starting invoke, for - " + function)

	if function == "init" {                    
		return t.Init(stub)
	} else if function == "read" {             
		return read(stub, args)
	} else if function == "write" {            
		return write(stub, args)
	} else if function == "delete_marble" {    
		return delete_marble(stub, args)
	} else if function == "init_marble" {      
		return init_marble(stub, args)
	} else if function == "set_owner" {        
		return set_owner(stub, args)
	} else if function == "init_owner"{        
		return init_owner(stub, args)
	} else if function == "read_everything"{   
		return read_everything(stub)
	} else if function == "getHistory"{        
		return getHistory(stub, args)
	} else if function == "getMarblesByRange"{ 
		return getMarblesByRange(stub, args)
	} else if function == "disable_owner"{     
		return disable_owner(stub, args)
	}

	fmt.Println("Received unknown invoke function name - " + function)
	return shim.Error("Received unknown invoke function name - '" + function + "'")
}


func (t *SimpleChaincode) Query(stub shim.ChaincodeStubInterface) pb.Response {
	return shim.Error("Unknown supported call - Query()")
}
