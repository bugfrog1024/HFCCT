package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
)

func main() {

	//接受用户传递的参数，都是以字符串的方式传递
	//命令行参数：需要解析文件的路径 需要解析的信息 ./chaincodes/sacc/sacc Global
	list := os.Args

	//positions are relative to fset
	fset := token.NewFileSet()
	//读取文件
	path, _ := filepath.Abs(list[1] + ".go")

	//解析代码 创建抽象语法树
	f, err := parser.ParseFile(fset, path, nil, parser.AllErrors)
	if err != nil {
		panic(err)
	}
	//打印AST
	// ast.Print(fset, f)

	switch list[2] {
	case "Global":
		//检测全局变量
		for _, i := range f.Decls {
			fn, ok := i.(*ast.GenDecl)
			//如果不是GenDecl或者不是var定义的全局变量
			if !ok || string(fn.Tok) != "U" {
				continue
			}
			fmt.Println(fn.Specs[0])
		}
		break
	case "Import":
		//检测导入的包
		for _, i := range f.Imports {
			fmt.Println(i.Path.Value)
		}
		break
	case "Other":
		//输出整个AST
		ast.Print(fset, f)
	}
}
