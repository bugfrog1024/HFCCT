package main

import (
	"fmt"
	"github.com/hyperledger/fabric/core/chaincode/lib/cid"
	"github.com/hyperledger/fabric/core/chaincode/shim"
	"github.com/pkg/errors"	 
)

func (t *MultiOrgChaincode) getRole(stub shim.ChaincodeStubInterface) (string,error) {

	role, found, err := cid.GetAttributeValue(stub, "role")
	if err != nil {
		return "", err
	}

	if !found {
		return "", errors.New("The type of the request owner is not present")
	}

	fmt.Println(" Acount Role - "+role)

	return role, nil
}
