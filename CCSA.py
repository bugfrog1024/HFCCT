import subprocess
import re
import os
import time
import chardet


# 链码静态分析类 针对每个合约创建一个实例
class CCSA():
    # 实例初始化 参数：待测合约路径
    def __init__(self, loc=None, file_flag=None):
        try:
            # 提取原始合约内容 检测编码
            raw = open(loc, 'rb').read()
            result = chardet.detect(raw)
            encoding = result['encoding']
            fp = open(loc, 'r', encoding=encoding)
            self.chaincode_coms = fp.read()
            fp.close()
            # 提取合约路径
            self.loc = loc
            # 提取合约目录名
            self.path_dir = './' + '/'.join(loc.split('/')[:-1]) + '/'
            # 记录时间标识
            self.file_flag = file_flag
            # 如果没有时间标识 按当前时间创建
            if not self.file_flag:
                # 时间标识 区分每次测试的目录
                date_time = time.localtime(time.time())
                self.file_flag = '%04d%02d%02d_%02d%02d%02d' % (
                    date_time.tm_year, date_time.tm_mon, date_time.tm_mday, date_time.tm_hour, date_time.tm_min,
                    date_time.tm_sec)
                # 创建文件夹 写入文件 调用命令行测试 保存测试文件和测试结果
                if not os.path.exists(self.path_dir + 'test_' + self.file_flag + '/'):
                    os.mkdir(self.path_dir + 'test_' + self.file_flag + '/')
            # 去除合约中的注释
            self.del_comments(self.chaincode_coms)
            # 获取链码的AST
            self.ast = []
            p = subprocess.Popen('go run CCAST.go ' + self.loc[:-3] + ' Other', shell=True, stdout=subprocess.PIPE)
            out, err = p.communicate()
            for line in out.splitlines():
                self.ast.append(line.decode())
        except:
            raise Exception('待测合约路径错误')

    # 去除代码中的注释 产生三个类变量 self.chaincode self.codes_mapping self.line_length
    def del_comments(self, codes):
        # 记录新代码每行的长度
        self.line_length = []
        # 记录新代码到原代码的行映射关系，目的是根据新代码的字符找原代码的行
        self.codes_mapping = []
        old_row = 0
        # 拆成行 按行去除注释
        old_codes_list = codes.split('\n')
        new_codes_list = []
        comments_flag = False
        for line in old_codes_list:
            # 从行首开始注释
            if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith(
                    '*') or line.strip().startswith('*/'):
                old_row += 1
                if line.strip().startswith('/*'):
                    comments_flag = True
                elif line.strip().startswith('*/'):
                    comments_flag = False
                continue
            if comments_flag:
                old_row += 1
                continue
            # 记录新代码到原代码的行映射关系
            self.codes_mapping.append(old_row)
            old_row += 1
            # 从行中开始注释
            if '//' in line:
                line = line[:line.find('//')]
            new_codes_list.append(line)
            # 记录新代码每行的长度 加换行符的长度
            self.line_length.append(len(line) + 1)
        self.chaincode = '\n'.join(new_codes_list)

    # 根据在去除注释后新链码的位置 计算出在去除注释前原链码的行数
    def in_which_line(self, loc):
        # 根据新链码每行长度 计算在新链码的行数
        sum_length = 0
        for row in range(len(self.line_length)):
            sum_length += self.line_length[row]
            if loc <= sum_length:
                # 根据新链码的行数 映射出原链码的行数 最后返回从1开始计算的行数
                return self.codes_mapping[row] + 1

    # 返回从index位置开始的下一个单词及位置
    def next_word(self, str, index):
        start = -1
        end = -1
        for i in range(index, len(str)):
            if str[i] in [' ', '\n', '\t', '(', ')', ',']:
                start = i + 1
                break
        for i in range(start + 1, len(str)):
            if str[i] in [' ', '\n', '\t', '(', ')', ',']:
                end = i
                break
        if start != -1 and end != -1:
            return str[start:end], start
        else:
            return None

    # 输出代码的AST
    def print_ast(self):
        for line in self.ast:
            print(line)

    # 检测导入的包
    def check_import(self):
        imports_info = []
        # 执行CCAST.go文件获取导入包的信息
        p = subprocess.Popen('go run CCAST.go ' + self.loc[:-3] + ' Import', shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        for line in out.splitlines():
            imports_info.append(line.decode())
        # 黑名单包 Web服务、外部库调用、系统命令执行、外部文件访问
        blacklist = ['"net/http"', '"database/sql"', '"github.com/mattn/go-oci8"', '"os"', '"os/exec"']
        imports_err = []
        for i in imports_info:
            if i in blacklist:
                # 在AST里检索 找到导包的位置
                for j in range(len(self.ast)):
                    if 'Value: "\\' + i[:-1] + '\\""' in self.ast[j]:
                        try:
                            imports_err.append(i + ' Line ' + str(self.ast[j - 2].split('.go:')[1].split(':')[0]))
                        except:
                            pass
                        break
        if imports_err:
            return "Import Blacklist (Web Service/External Library Calling/System Command Execution/External File Accessing)\n" + '\n'.join(
                imports_err)
        else:
            return None

    # 检测是否存在程序并发性
    def check_goroutine(self):
        go_concurrency = []
        for i in range(len(self.ast)):
            if '*ast.GoStmt' in self.ast[i]:
                try:
                    go_concurrency.append('Line ' + str(self.ast[i + 1].split('.go:')[1].split(':')[0]))
                except:
                    pass
        if go_concurrency:
            return 'Concurrency of Program\nGoroutine in ' + ' , '.join(go_concurrency)
        else:
            return None

    # 检测链码中是否有字段声明
    def check_field_declare(self):
        start = self.chaincode.find('shim.Start(new(') + len('shim.Start(new(') - 1
        struct_name = self.next_word(self.chaincode, start)[0]
        struct_loc = self.chaincode.find('type ' + struct_name + ' struct {') + len('type ' + struct_name + ' struct {')
        a = self.next_word(self.chaincode, struct_loc)[0].strip()
        if self.next_word(self.chaincode, struct_loc)[0].strip() != '}':
            # 在AST中找行数 第一次出现是链码结构体的定义
            for i in range(len(self.ast)):
                if 'Name: "' + struct_name + '"' in self.ast[i]:
                    try:
                        return 'Field Declarations\nDeclare ' + struct_name + ' in Line ' + str(
                            self.ast[i - 1].split('.go:')[1].split(':')[0])
                    except:
                        pass
        else:
            return None

    # 检测是否存在写入后读取
    def check_read_after_write(self):
        read_after_write_errs = []
        put_loc = self.chaincode.find('.PutState(')
        while put_loc != -1:
            put_loc = put_loc + len('.PutState(') - 1
            key = self.next_word(self.chaincode, put_loc)[0]
            if key != ')':
                # 找下一个读取这个键的GetState
                get_loc = self.chaincode.find('.GetState(' + key, put_loc)
                # 判断PutState和GetState是否在一个函数内 通过两者之间是否有连着的换行符和右花括号判断
                if get_loc != -1 and '\n}' not in self.chaincode[put_loc:get_loc]:
                    read_after_write_errs.append('PutState(' + key + ') Line ' + str(
                        self.in_which_line(put_loc)) + ' , GetState(' + key + ') Line ' + str(
                        self.in_which_line(get_loc)))
            put_loc = self.chaincode.find('.PutState(', put_loc)
        if read_after_write_errs:
            return 'Read Your Write\n' + '\n'.join(read_after_write_errs)
        else:
            return None

    # 检测是否存在范围查询风险
    def check_range_query(self):
        range_query_list = ['GetStateByRange', 'GetStateByRangeWithPagination', 'GetStateByPartialCompositeKey',
                            'GetStateByPartialCompositeKeyWithPagination', 'GetPrivateDataByRange', 'GetHistoryForKey',
                            'GetQueryResult', 'GetQueryResultWithPagination', 'GetPrivateDataQueryResult',
                            'GetPrivateDataByPartialCompositeKey']
        range_query = []
        for i in range_query_list:
            if '.' + i + '(' in self.chaincode:
                # 在AST中找行数
                for j in range(len(self.ast)):
                    if 'Name: "' + i + '"' in self.ast[j]:
                        try:
                            range_query.append(i + '() Line ' + str(self.ast[j - 1].split('.go:')[1].split(':')[0]))
                        except:
                            pass
        if range_query:
            return 'Range Query Risk\n' + '\n'.join(range_query)
        return None

    # 检测是否存在未处理的错误（可能会误报）
    def check_unhandle_err(self):
        unhandled_errs = []
        for i in range(len(self.ast)):
            if 'Name: "_"' in self.ast[i]:
                try:
                    unhandled_errs.append('Line ' + str(self.ast[i - 1].split('.go:')[1].split(':')[0]))
                except:
                    pass
        if unhandled_errs:
            return 'Unhandled Errors Warning\nUse "_" in ' + ' , '.join(unhandled_errs)
        else:
            return None

    # 检测是否存在跨channel链码调用
    def check_cross_channel(self):
        cross_chan_errs = []
        for i in range(len(self.ast)):
            if 'Name: "2"' in self.ast[i]:
                try:
                    cross_chan_errs.append('Line ' + str(self.ast[i - 1].split('.go:')[1].split(':')[0]))
                except:
                    pass
        if cross_chan_errs:
            return 'Chaincode Invocation Warning\nInvokeChaincode() in ' + ' , '.join(cross_chan_errs)
        else:
            return None

    # 检测是否存在重新设置对象地址
    def check_re_addr(self):
        re_addr_errs = []
        # 只要定义了指针类型的变量就予以警告
        # p := new(int)
        type1_all = re.finditer('\s?:?=\s?new\(.+\)', self.chaincode)
        for i in type1_all:
            re_addr_errs.append('Line ' + str(self.in_which_line(i.span(0)[0])))
        # var p *int
        type2_all = re.finditer('var\s.+\s\*.+', self.chaincode)
        for i in type2_all:
            re_addr_errs.append('Line ' + str(self.in_which_line(i.span(0)[0])))
        # p := &a
        type3_all = re.finditer('\s?:?=\s?&.+', self.chaincode)
        for i in type3_all:
            re_addr_errs.append('Line ' + str(self.in_which_line(i.span(0)[0])))
        if re_addr_errs:
            return 'Reifified Object Addresses Warning\nDeclare Pointer Variable in ' + ' , '.join(re_addr_errs)

    # 依次执行各项检测 把检测出的漏洞写入文件 Test_Report.txt
    def chaincode_static_analysis_test(self):
        fp_res = open(self.path_dir + 'test_' + self.file_flag + '/Test_Report.txt', 'w')
        fp_res.write(
            '**************************************************\n----- Test File: ' + self.loc + ' -----\n**************************************************\n')
        check_funcs = [self.check_import, self.check_goroutine, self.check_field_declare, self.check_read_after_write,
                       self.check_range_query, self.check_cross_channel, self.check_re_addr, self.check_unhandle_err]
        for check_func in check_funcs:
            res = check_func()
            if res:
                fp_res.write(res + '\n**************************************************\n')
        fp_res.close()


if __name__ == '__main__':
    # ccsa = CCSA('chaincodes/Simple-Fabric-Web-Project-master/bMRP.go')
    p = subprocess.Popen('go run CCAST.go codes/flower Other', shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        print(line.decode())
