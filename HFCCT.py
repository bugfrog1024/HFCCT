# hyperledger fabric chaincode test
from CCSE import CCSE
from CCSA import CCSA
import os, time


class HFCCT():
    # 实例初始化 参数：待测合约路径,生成M组测试文件,一个测试文件执行N次
    def __init__(self, loc=None, M=5, N=2):
        try:
            # 提取合约目录名
            self.path_dir = './' + '/'.join(loc.split('/')[:-1]) + '/'
            # 时间标识 区分每次测试的目录
            date_time = time.localtime(time.time())
            self.file_flag = '%04d%02d%02d_%02d%02d%02d' % (
                date_time.tm_year, date_time.tm_mon, date_time.tm_mday, date_time.tm_hour, date_time.tm_min,
                date_time.tm_sec)
            # 创建文件夹 用于保存测试文件和测试结果
            if not os.path.exists(self.path_dir + 'test_' + self.file_flag + '/'):
                os.mkdir(self.path_dir + 'test_' + self.file_flag + '/')
            # 测试文件和测试报告的目录
            self.test_dir = self.path_dir + 'test_' + self.file_flag + '/'
            # 创建CCSE和CCSA对象
            self.ccse = CCSE(loc, M, N, self.file_flag)
            self.ccsa = CCSA(loc, self.file_flag)
        except:
            raise Exception('待测合约路径错误')

    # 执行测试
    def hyperledger_fabric_chaincode_test(self):
        # 静态分析 会生成Test_Report
        self.ccsa.chaincode_static_analysis_test()
        # 普通函数符号执行测试
        self.ccse.normal_func_symbolic_execute_test()
        # 链码符号执行测试
        self.ccse.chaincode_symbolic_execute_test()
        # 在Test_Report中补充符号执行的测试结果
        fp_res = open(self.test_dir + 'Test_Report.txt', 'a')
        file_list = os.listdir(self.test_dir)
        for file in file_list:
            # 测试文件执行结果
            if file.startswith('test_res') and not file.endswith('err.txt') and not file.endswith('0.txt'):
                f = open(self.test_dir + file, 'r')
                content_list = f.read().split('\n')
                f.close()
                for i in range(len(content_list)):
                    # gotest测试报错
                    if '--- FAIL: TestFunc' in content_list[i]:
                        err_info = content_list[i + 2].strip()
                        fp_res.write('Test Case: test_file_' + file.split('_')[
                            2] + '.go\nTest Result: ' + file + '\n' + err_info + '\n')
                        if 'index out of range' in err_info:
                            fp_res.write('Unchecked Input Arguments\n')
                        elif 'Return value error!' in err_info:
                            fp_res.write('Unchecked Return Values Or Invoke Unknown Functions\n')
                        else:
                            fp_res.write('Unknown Errors\n')
                        fp_res.write('**************************************************\n')
                    # 执行普通go程序报错
                    elif 'FAIL' in content_list[i]:
                        fp_res.write('Test Case: test_file_' + file.split('_')[2] + '.go\nTest Result: ' + file + '\n')
                        for j in range(i + 1, len(content_list)):
                            if content_list[j].startswith('./') or content_list[j].startswith('.\\'):
                                fp_res.write(content_list[j] + '\n')
                        fp_res.write('**************************************************\n')
            # 有xxx_err.txt文件 表示存在同样的测试文件执行结果不一致的情况
            elif file.endswith('err.txt'):
                f = open(self.test_dir + file, 'r')
                content_list = f.read().split('\n')
                f.close()
                file_prefix = file[:-7]
                # 如果是xxx_0.txt和xxx_1.txt不一致 则是全局变量错误
                if file_prefix + '0.txt' in content_list[0] or file_prefix + '0.txt' in content_list[3]:
                    fp_res.write('Test Case: test_file_' + file.split('_')[
                        2] + '.go\nTest Result: ' + file_prefix + '0.txt & ' + file_prefix + '1.txt Not Equal\nGlobal Variable\n**************************************************\n')
                # 否则是xxx_1.txt和其他执行结果不一致 则是不确定性错误
                else:
                    file_1 = content_list[0].split('/')[-1]
                    file_2 = content_list[1].split('/')[-1]
                    fp_res.write('Test Case: test_file_' + file.split('_')[
                        2] + '.go\nTest Result: ' + file_1 + ' & ' + file_2 + ' Not Equal\nRandom Number Generation Or System Timestamp Or Map Structure Iteration\n**************************************************\n')
            # 对普通函数单独测试的文件
            elif file.endswith('res.txt') and 'functest' in file:
                f = open(self.test_dir + file, 'r')
                content_list = f.read().split('\n')
                f.close()
                for i in range(len(content_list)):
                    # 有自定义的整数溢出panic报错信息
                    if 'panic' in content_list[i]:
                        # 往上找起始 出现测试文件名的行
                        start = -1
                        for j in range(i - 1, -1, -1):
                            if content_list[j].startswith('----- '):
                                start = j
                                break
                        # 往下找结束 空行
                        end = -1
                        for j in range(i + 1, len(content_list)):
                            if content_list[j] == '':
                                end = j
                                break
                        if start != -1 and end != -1:
                            fp_res.write(
                                'Test Case: ' + content_list[start][6:-6] + '\nTest Result: ' + file + '\n' + '\n'.join(
                                    content_list[i:end]) + ' \n**************************************************\n')
                        break
                    # 执行普通go程序报错
                    elif '# command-line-arguments' in content_list[i]:
                        # 往上找起始 出现测试文件名的行
                        start = -1
                        for j in range(i - 1, -1, -1):
                            if content_list[j].startswith('----- '):
                                start = j
                                break
                        # 往下找结束 空行
                        end = -1
                        for j in range(i + 1, len(content_list)):
                            if content_list[j] == '':
                                end = j
                                break
                        if start != -1 and end != -1:
                            fp_res.write(
                                'Test Case: test_file_' + content_list[start][6:-6] + '\nTest Result: ' + file + '\n')
                            for j in range(i + 1, end):
                                if content_list[j].startswith('./') or content_list[j].startswith('.\\'):
                                    fp_res.write(content_list[j] + '\n')
                            fp_res.write('**************************************************\n')
                        break
                pass
        fp_res.close()
        # 如果没有检测出漏洞 予以说明
        flag = False
        fp_res = open(self.test_dir + 'Test_Report.txt', 'r')
        if len(fp_res.read().split('\n')) < 5:
            flag = True
        fp_res.close()
        if flag:
            fp_res = open(self.test_dir + 'Test_Report.txt', 'a')
            fp_res.write('----- Find No Vulnerabilities -----\n**************************************************\n')
            fp_res.close()


if __name__ == '__main__':

    test_list = [
        'chaincodes/atore/chaincode_AtoreAndAccess.go',
        'chaincodes/charity/charity_contract.go',
        'chaincodes/fabric-samples/abac/abac.go',
        'chaincodes/fabric-samples/marbles02/marbles_chaincode.go',
        'chaincodes/fabric-samples/marbles02_private/marbles_chaincode_private.go',
        'chaincodes/fabric-samples/sacc/sacc.go',
        'chaincodes/fabric_e2e_app-master/chaincode_example02/chaincode_example02.go',
        'chaincodes/fabric_e2e_app-master/fabcar/fabcar.go',
        'chaincodes/fabric_e2e_app-master/test/test.go',
        'chaincodes/marbles-master/marbles.go',
        'chaincodes/multiorgledger-master/main.go',
        'chaincodes/MySmartContract-master/chaincode_myexample.go',
        'chaincodes/Simple-Fabric-Web-Project-master/bMRP.go',
        'chaincodes/supplychain-blockchain-network/solution.go',
        'chaincodes/vehiclesharing-master/vehiclesharing.go',
    ]

    f_time = open('time_record.txt', 'w')
    for cc in test_list:
        # start
        f_time.write('----- ' + cc + ' -----\n')
        date_time = time.localtime(time.time())
        f_time.write('start: %04d%02d%02d_%02d%02d%02d\n' % (
            date_time.tm_year, date_time.tm_mon, date_time.tm_mday, date_time.tm_hour, date_time.tm_min,
            date_time.tm_sec))
        hfcct = HFCCT(cc, 10, 2)
        hfcct.hyperledger_fabric_chaincode_test()
        print('Test Report Generated: ' + hfcct.test_dir + 'Test_Report.txt')
        # end
        date_time = time.localtime(time.time())
        f_time.write('end: %04d%02d%02d_%02d%02d%02d\n\n' % (
            date_time.tm_year, date_time.tm_mon, date_time.tm_mday, date_time.tm_hour, date_time.tm_min,
            date_time.tm_sec))
    f_time.close()
