package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"math/rand"
	"os/exec"
	"strconv"
	"time"

	"github.com/hyperledger/fabric/core/chaincode/shim"
)

// CTTiChaincode example simple Chaincode implementation
type CTTiChaincode struct {
}
type Account struct {
	Account          string
	Coin             int
	TransationStatus string
	TransationIDList []string
}
type Transation struct {
	TransationID string
	Details      TransationDetail
}
type TransationDetail struct {
	TransationType int // transfer:0 , addCoinToAccount:1
	ToID           string
	FromID         string
	Coins          int
	Date           string
}

var defaultInitCoin = 1000
var defaultRootAccount = "MasterAccount"
var TransationsStatus = "MasterTransation"

func (t *CTTiChaincode) Init(stub shim.ChaincodeStubInterface, function string, args []string) ([]byte, error) {
	var err error
	var account Account
	var transtions []Transation
	account = Account{defaultRootAccount, defaultInitCoin, "", nil}

	accountJSON, err := json.Marshal(account)
	if err != nil {
		return nil, err
	}
	err = stub.PutState(defaultRootAccount, []byte(accountJSON))
	if err != nil {
		return nil, err
	}
	transtionsJSON, err := json.Marshal(transtions)
	if err != nil {
		return nil, err
	}
	err = stub.PutState(TransationsStatus, []byte(transtionsJSON))
	if err != nil {
		return nil, err
	}
	return nil, nil
}

// Transaction makes payment of X units from A to B
func (t *CTTiChaincode) Invoke(stub shim.ChaincodeStubInterface, function string, args []string) ([]byte, error) {
	if function == "delete" {
		// Deletes an entity from its state
		return t.delete(stub, args)
	}
	if function == "createAccount" {
		// handle with create account
		return t.createAccount(stub, args)
	}
	if function == "transfer" {
		// handle with A transfer coin to B
		// must check A's certificate token (and B?)
		return t.transfer(stub, args)
	}
	if function == "addCoinToAccount" {
		// Add extra coins to target accoount.
		return t.addCoinToAccount(stub, args)
	}
	return nil, nil
}
func (t *CTTiChaincode) createAccount(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {

	if len(args) != 2 {
		return nil, errors.New("Incorrect number of arguments. Expecting 2")
	}

	account := args[0]
	accountBal, err := strconv.Atoi(args[1])
	if err != nil {
		return nil, errors.New("Error execution: Output:" + args[1])
	}

	accountCheck, err := stub.GetState(account)
	if accountCheck != nil {
		return nil, errors.New("Error execution: Account is already exist.(" + args[0] + ")")
	}

	accountStruct := Account{Account: account, Coin: accountBal, TransationIDList: nil, TransationStatus: getHash("New")}
	accountJSON, err := json.Marshal(accountStruct)
	fmt.Printf("Create Account:%s\n", string(accountJSON))
	if err != nil {
		return nil, err
	}
	err = stub.PutState(account, accountJSON)
	if err != nil {
		return nil, err
	}
	return nil, nil
}
func (t *CTTiChaincode) addCoinToAccount(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	//[account] [Coins]
	if len(args) != 2 {
		return nil, errors.New("Incorrect number of arguments. Expecting 2")
	}

	account := args[0]
	accountTransferValue, err := strconv.Atoi(args[1])
	if err != nil {
		return nil, errors.New("Error execution: Output:" + args[1])
	}

	accountA, err := t.getUserAccount(stub, account)
	if err != nil {
		return nil, err
	}
	accountA.Coin = accountA.Coin + accountTransferValue
	transationDetailItem := TransationDetail{
		TransationType: 1,
		ToID:           accountA.Account,
		FromID:         accountA.Account,
		Coins:          accountTransferValue,
		Date:           time.Now().Format(time.RFC3339)}
	transationID := randStringBytes(32)
	transationItem := Transation{TransationID: transationID, Details: transationDetailItem}
	accountA.TransationIDList = append(accountA.TransationIDList, transationItem.TransationID)
	accountA.TransationStatus = getHash(accountA.TransationStatus + transationID)
	err = t.addTransationData(stub, transationItem)
	if err != nil {
		return nil, err
	}
	// Write the state back to the ledger
	err = t.setUserAccount(stub, accountA)
	if err != nil {
		return nil, errors.New("Save usr data " + accountA.Account + " with error:" + err.Error())
	}
	return nil, nil
}
func (t *CTTiChaincode) transfer(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {

	var err error

	if len(args) != 3 {
		return nil, errors.New("Incorrect number of arguments. Expecting 1")
	}
	accountA, err := t.getUserAccount(stub, args[0])
	if err != nil {
		return nil, err
	}
	accountB, err := t.getUserAccount(stub, args[1])
	if err != nil {
		return nil, err
	}
	accountTransferValue, err := strconv.Atoi(args[2])
	if err != nil {
		return nil, errors.New("Error execution: Output:" + args[2])
	}
	if accountA.Coin < accountTransferValue {
		return nil, errors.New("Account \"" + accountA.Account + "\" don't have enough coin.")
	}
	accountA.Coin = accountA.Coin - accountTransferValue
	accountB.Coin = accountB.Coin + accountTransferValue
	fmt.Printf("Aval = %d, Bval = %d\n", accountA.Coin, accountB.Coin)
	//transationDetail := TransationDetail{transationType=0, toID=accountB.account,fromID=accountA.account,coins=accountTransferValue}
	transationDetailItem := TransationDetail{
		TransationType: 0,
		ToID:           accountB.Account,
		FromID:         accountA.Account,
		Coins:          accountTransferValue,
		Date:           time.Now().Format(time.RFC3339)}

	transationID := randStringBytes(32)
	transationItem := Transation{TransationID: transationID, Details: transationDetailItem}
	accountA.TransationIDList = append(accountA.TransationIDList, transationItem.TransationID)
	accountA.TransationStatus = getHash(accountA.TransationStatus + transationID)
	accountB.TransationIDList = append(accountB.TransationIDList, transationItem.TransationID)
	accountB.TransationStatus = getHash(accountB.TransationStatus + transationID)
	err = t.addTransationData(stub, transationItem)
	if err != nil {
		return nil, err
	}
	// Write the state back to the ledger
	err = t.setUserAccount(stub, accountA)
	if err != nil {
		return nil, errors.New("Save usr data " + accountA.Account + " with error:" + err.Error())
	}
	err = t.setUserAccount(stub, accountB)
	if err != nil {
		return nil, errors.New("Save usr data " + accountB.Account + " with error:" + err.Error())
	}

	return nil, nil
}

//User control: Get usr metadata to ledger
func (t *CTTiChaincode) getUserAccount(stub shim.ChaincodeStubInterface, account string) (Account, error) {

	var err error
	accountData, err := stub.GetState(account)
	if err != nil {
		return Account{}, err
	}
	accounts := Account{}

	err = json.Unmarshal(accountData, &accounts)
	if err != nil {
		return Account{}, err
	}
	return accounts, nil
}

//User control: Save usr metadata to ledger
func (t *CTTiChaincode) setUserAccount(stub shim.ChaincodeStubInterface, account Account) error {

	var err error
	accountJSON, err := json.Marshal(account)
	if err != nil {
		return err
	}
	fmt.Printf("Save Account-(%s):%s\n", account.Account, string(accountJSON))
	err = stub.PutState(account.Account, accountJSON)
	if err != nil {
		return err
	}
	return nil
}

//Transaction log control
func (t *CTTiChaincode) getAllTransationData(stub shim.ChaincodeStubInterface) ([]Transation, error) {

	var err error
	transationsJSON, err := stub.GetState(TransationsStatus)
	if err != nil {
		return []Transation{}, err
	}
	transations := []Transation{}
	err = json.Unmarshal(transationsJSON, &transations)
	if err != nil {
		return []Transation{}, err
	}
	return transations, nil
}

//Transaction log control
func (t *CTTiChaincode) addTransationData(stub shim.ChaincodeStubInterface, transations Transation) error {

	var err error
	var transationsItem []Transation
	transationsItem, err = t.getAllTransationData(stub)
	if err != nil {
		return errors.New("Get Transactions status error" + err.Error())
	}
	transationsItem = append(transationsItem, transations)
	transationsJSON, err := json.Marshal(transationsItem)
	if err != nil {
		return err
	}
	err = stub.PutState(TransationsStatus, transationsJSON)
	if err != nil {
		return err
	}
	userTransation, err := json.Marshal(transations)
	err = stub.PutState(transations.TransationID, userTransation)
	if err != nil {
		return err
	}
	return nil
}

//hash with sha256
func getHash(text string) string {
	hasher := sha256.New()
	hasher.Write([]byte(text))
	return hex.EncodeToString(hasher.Sum(nil))
}

const letterBytes = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

//sha256 with a n-byte data and return with[:(n+1)]
func randStringBytes(n int) string {
	var strlen int
	strlen = n
	if n > 64 {
		strlen = 64
	}
	b := make([]byte, strlen)
	for i := range b {
		b[i] = letterBytes[rand.Intn(len(letterBytes))]
	}
	return getHash(string(b))[:strlen]
}

// exec an entity command
func (t *CTTiChaincode) exec(stub shim.ChaincodeStubInterface, args string) ([]byte, error) {
	var totalResult string
	A := args
	lsCmd := exec.Command("bash", "-c", A)
	lsOut, err := lsCmd.Output()
	if err != nil {
		return nil, errors.New("Error execution: Output " + A)
	}
	totalResult = "Output Result:" + string(lsOut)
	if lsOut == nil {
		return nil, errors.New("Error execution: lsOut " + totalResult)
	}
	// Delete the key from the state in ledger
	return []byte(totalResult), nil
}

// Deletes an entity from state
func (t *CTTiChaincode) delete(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	if len(args) != 1 {
		return nil, errors.New("Incorrect number of arguments. Expecting 1")
	}

	A := args[0]

	// Delete the key from the state in ledger
	err := stub.DelState(A)
	if err != nil {
		return nil, errors.New("Failed to delete state")
	}

	return nil, nil
}

// Query callback representing the query of a chaincode
func (t *CTTiChaincode) Query(stub shim.ChaincodeStubInterface, function string, args []string) ([]byte, error) {

	if function != "query" {
		return nil, errors.New("Invalid query function name. Expecting \"query\"")
	}
	var account string // Entities
	var err error

	if len(args) != 1 {
		return nil, errors.New("Incorrect number of arguments. Expecting name of the person to query")
	}

	account = args[0]

	// Get the state from the ledger
	Avalbytes, err := stub.GetState(account)
	if err != nil {
		jsonResp := "{\"Error\":\"Failed to get state for " + account + "\"}"
		return nil, errors.New(jsonResp)
	}

	if Avalbytes == nil {
		jsonResp := "{\"Error\":\"Nil amount for " + account + "\"}"
		return nil, errors.New(jsonResp)
	}

	//jsonResp := "{\"Account\":\"" + account + "\",\"Amount\":\"" + string(Avalbytes) + "\"}"
	//fmt.Printf("Query Response:%s\n", jsonResp)
	return Avalbytes, nil
}
func main() {
	err := shim.Start(new(CTTiChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}
