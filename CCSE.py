import re
import z3
import random
import subprocess
import os
import time
import chardet


# 链码符号执行类 针对每个合约创建一个实例
class CCSE():
    # 实例初始化 参数：待测合约路径,生成M组测试文件,一个测试文件执行N次
    def __init__(self, loc=None, M=5, N=2, file_flag=None):
        try:
            # 提取原始合约内容 检测编码
            raw = open(loc, 'rb').read()
            result = chardet.detect(raw)
            encoding = result['encoding']
            fp = open(loc, 'r', encoding=encoding)
            self.chaincode = fp.read()
            fp.close()
            # 去除链码中的注释
            self.del_comments()
            # 提取合约路径
            self.loc = loc
            # 提取合约文件名
            self.mockstub_name = loc.split('/')[-1][:-3]
            # 提取合约目录名
            self.path_dir = './' + '/'.join(loc.split('/')[:-1]) + '/'
            # 记录时间标识、M、N
            self.file_flag = file_flag
            self.M = M
            self.N = N
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
        except:
            raise Exception('待测合约路径错误')

    # 去除链码中的注释
    def del_comments(self):
        old_chaincode_list = self.chaincode.split('\n')
        new_chaincode_list = []
        comments_flag = False
        for line in old_chaincode_list:
            # 从行首开始注释
            if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith(
                    '*') or line.strip().startswith('*/'):
                if line.strip().startswith('/*'):
                    comments_flag = True
                elif line.strip().startswith('*/'):
                    comments_flag = False
                continue
            if comments_flag:
                continue
            # 从行中开始注释
            if '//' in line:
                line = line[:line.find('//')]
            new_chaincode_list.append(line)
        self.chaincode = '\n'.join(new_chaincode_list)
        # print(self.chaincode)

    # 返回从index位置开始的上一个单词及位置
    def last_word(self, str, index):
        start = -1
        end = -1
        for i in range(index, 0, -1):
            if str[i] in [' ', '\n', '\t', '(', ')', ',']:
                i -= 1
                while str[i] in [' ', '\n', '\t', '(', ')', ',']:
                    i -= 1
                end = i + 1
                break
        for i in range(end - 1, 0, -1):
            if str[i] in [' ', '\n', '\t', '(', ')', ',']:
                start = i + 1
                break
        if start != -1 and end != -1:
            return str[start:end], start
        else:
            return None

    # 返回从index位置开始的下一个单词及位置
    def next_word(self, str, index):
        start = -1
        end = -1
        for i in range(index, len(str)):
            if str[i] in [' ', '\n', '\t', '(', ')', ',']:
                i += 1
                while str[i] in [' ', '\n', '\t', '(', ')', ',']:
                    i += 1
                start = i
                break
        for i in range(start + 1, len(str)):
            if str[i] in [' ', '\n', '\t', '(', ')', ',']:
                end = i
                break
        if start != -1 and end != -1:
            return str[start:end], start
        else:
            return None

    # 从整个链码中提取某个函数的头 从“func”到“{”之间
    def get_func_head(self, func_name):
        # 在整个链码中匹配函数头
        res = re.search('func (\(.*\) )?' + func_name, self.chaincode)
        if res:
            # 提取匹配结果的起始位置
            func_loc = res.span()[0]
            start = func_loc
            end = -1
            for i in range(func_loc + 7 + len(func_name), len(self.chaincode)):
                if self.chaincode[i] == '{':
                    end = i
                    break
            if end != -1:
                return self.chaincode[start:end]
            else:
                return None
        else:
            return None

    # 从整个链码中提取某个函数的内容
    def get_func_content(self, func_name):
        # 在整个链码中匹配函数头
        res = re.search('func (\(.*\) )?' + func_name, self.chaincode)
        if res:
            # 提取匹配结果的起始位置
            func_loc = res.span()[0]
            start = func_loc
            end = -1
            count = 0
            for i in range(func_loc + 7 + len(func_name), len(self.chaincode)):
                if self.chaincode[i] == '{':
                    # if count == 0:    只提取函数主体，start初值为-1，最后return的条件为start != -1 and end != -1
                    #     start = i
                    count += 1
                elif self.chaincode[i] == '}':
                    count -= 1
                    if count == 0:
                        end = i + 1
                        break

            if end != -1:
                return self.chaincode[start:end]
            else:
                return None
        else:
            return None

    # 获取if后面的条件 参数：函数主体内容，if的位置 返回：条件内容
    def get_if_cond(self, func_content, if_loc):
        start = -1
        end = -1
        for i in range(if_loc, len(func_content)):
            if start == -1 and func_content[i] == ' ':
                start = i + 1
            elif func_content[i] == '{':
                end = i
                break
        # print(start,end,self.prog[start:end].strip())
        if start != -1 and end != -1:
            return func_content[start:end].strip()
        else:
            return None

    # 取反字符串条件
    def reverse_cond(self, str):
        if '!=' in str:
            return str.replace('!=', '==')
        elif '==' in str:
            return str.replace('==', '!=')

    # 找到len、[]等字符串条件中的参数
    def find_para(self, cond, way=None):
        # 如果是len相关条件
        if way == 'len':
            return cond[cond.find('len') + 4:-1]
        # 如果是数组值相关条件
        elif way == '[]':
            temp = cond.split('[')
            return (temp[0], int(temp[1][:-1]))
        # 如果是字符串条件
        else:
            return cond

    # 随机产生n位字母的字符串
    def random_char(self, length):
        string = ''
        for i in range(length):
            string += chr(random.randint(97, 97 + 25))
        return '"' + string + '"'

    # 提取函数的参数列表  参数：函数主体，函数名  返回值：
    def get_params_list(self, func_content, func_name):
        try:
            func_head = func_content.split('\n')[0]
            start = func_head.find(func_name) + len(func_name) + 1
            end = -1
            for i in range(start, len(func_head)):
                if func_head[i] == ')':
                    end = i
                    break
            if end != -1:
                res = {}
                params_list = func_head[start:end].split(',')
                for p in params_list:
                    p = p.strip().split()
                    # 只保留int、string、[]string类型
                    if p[1] in ['uint8', 'uint16', 'uint32', 'uint64', 'int8', 'int16', 'int32', 'int64', 'int',
                                'string', '[]string']:
                        res[p[0]] = p[1]
                # print(res)
                return res
            else:
                return None
        except:
            return None

    # 符号执行  参数：函数主体和参数列表  返回值：[{'conds': [约束条件], 'params': {解集}}, ...]
    def symbolic_execute(self, func_content=None, args=None):

        print('---符号执行开始---')
        # 过滤“_”参数
        for key in args.keys():
            if key == '' or key == '_':
                del args[key]
                break
        # 求解参数
        z3_args = {}
        # 参数类型
        for key in args.keys():
            # 整数
            if args[key] in ['uint8', 'uint16', 'uint32', 'uint64', 'int8', 'int16', 'int32', 'int64', 'int']:
                z3_args[key] = z3.Int(key)
            # 实数 未测试
            elif args[key] == 'real':
                z3_args[key] = z3.Real(key)

        # 用于存储所有条件
        cond = []

        # 第一个if条件的位置 添加条件
        next_cond_loc = func_content.find('if ')
        while next_cond_loc != -1:
            next_cond = self.get_if_cond(func_content, next_cond_loc + 1)
            next_cond_loc = func_content.find('if ', next_cond_loc + 2)
            # 不考虑判断值是否为nil的条件
            if 'nil' in next_cond:
                continue
            # && || 拆开条件加入
            if '&&' in next_cond:
                cond.append(next_cond.split('&&')[0].strip())
                cond.append(next_cond.split('&&')[1].strip())
            elif '||' in next_cond:
                cond.append(next_cond.split('||')[0].strip())
                cond.append(next_cond.split('||')[1].strip())
            else:
                cond.append(next_cond)
        # print(cond)

        # 如果是invoke接口 不再进行条件组合 直接等于条件中的各函数名
        if 'Invoke(' in func_content:
            # 如果cond中没有if条件 继续考虑switch条件
            if not cond and 'switch' in func_content and 'case' in func_content:
                switch_cond = self.next_word(func_content, func_content.find('switch'))[0].strip()
                next_cond_loc = func_content.find('case ')
                while next_cond_loc != -1:
                    next_cond = self.next_word(func_content, next_cond_loc)[0].strip()[:-1]
                    next_cond_loc = func_content.find('case ', next_cond_loc + 4)
                    cond.append(switch_cond + ' == ' + next_cond)
            print(cond)
            # 有约束条件则直接取等值简化处理，条件为空则直接返回None
            if cond:
                res = []
                for c in range(len(cond)):
                    cp = {}
                    cp['conds'] = [cond[c]]
                    if '>=' in cond[c] or '<=' in cond[c]:
                        cond[c] = re.sub('<=|>=', '==', cond[c])
                    elif '>' in cond[c] or '<' in cond[c]:
                        cond[c] = re.sub('<|>', '==', cond[c])
                    elif '!=' in cond[c]:
                        cond[c] = re.sub('!=', '==', cond[c])
                    cp['params'] = {cond[c].split('==')[0].strip(): cond[c].split('==')[1].strip()}
                    res.append(cp)
                # 对第一个函数名取反 得到不和任何函数名相等的参数
                cp = {}
                cp['conds'] = [cond[0].split('==')[0].strip() + ' != any function']
                cp['params'] = {
                    cond[0].split('==')[0].strip(): self.random_char(len(cond[0].split('==')[1].strip()) - 2)}
                res.append(cp)
                # [{'conds': ['fn == "set"'], 'params': {'fn': '"set"'}}, {'conds': ['fn != any function'], 'params': {'fn': '"juz"'}}]
                print('Invoke约束条件和解集：\n' + str(res) + '\n---符号执行结束---\n')
                return res
            else:
                return None

        # 所有能求解的条件的参数
        params_can_solve = list(args.keys())
        # 有约束条件则求解集，条件为空则直接返回None
        if cond:
            str_cond = []
            int_cond = []
            # 区分是数值条件还是字符串条件
            for c in cond:
                # 字符串、数组不用z3求解
                if 'len' in c or '"' in c or '[' in c:
                    # 替换条件中的函数内变量
                    need = True
                    if '==' in c:
                        para = c.split('==')[0].strip()
                    elif '!=' in c:
                        para = c.split('!=')[0].strip()
                    elif '<' in c:
                        para = c.split('<')[0].strip()
                    elif '<=' in c:
                        para = c.split('<=')[0].strip()
                    elif '>' in c:
                        para = c.split('>')[0].strip()
                    elif '>=' in c:
                        para = c.split('>=')[0].strip()
                    try:
                        for k in args.keys():
                            if k in para:
                                need = False
                    except:
                        pass
                    if need:
                        try:
                            var_loc = func_content.find(para + ' :=')
                            if var_loc != -1:
                                var_val = self.next_word(func_content, var_loc + len(para + ' :='))[0]
                                c = c.replace(para, var_val)
                                params_can_solve.append(para)
                            var_loc = func_content.find(para + ':=')
                            if var_loc != -1:
                                var_val = self.next_word(func_content, var_loc + len(para + ':='))[0]
                                c = c.replace(para, var_val)
                                params_can_solve.append(para)
                            var_loc = func_content.find('var ' + para + ' =')
                            if var_loc != -1:
                                var_val = self.next_word(func_content, var_loc + len('var ' + para + ' ='))[0]
                                c = c.replace(para, var_val)
                                params_can_solve.append(para)
                            var_loc = func_content.find('var ' + para + '=')
                            if var_loc != -1:
                                var_val = self.next_word(func_content, var_loc + len('var ' + para + '='))[0]
                                c = c.replace(para, var_val)
                                params_can_solve.append(para)
                        except:
                            print('替换参数错误')
                    str_cond.append(c)

                # 整数、实数用z3求解
                else:
                    # 找到所有的变量声明 替换条件中的变量
                    var_loc = func_content.find(":=")
                    while var_loc != -1:
                        var_name = self.last_word(func_content, var_loc)[0]
                        var_val = self.next_word(func_content, var_loc + 2)[0]
                        c = c.replace(var_name.strip(), '(' + var_val + ')')
                        var_loc = func_content.find(":=", var_loc + 2)

                    # 替换条件 $$$防止变量名和z3_args冲突
                    for key in args.keys():
                        c = c.replace("z3_args", "$$$")
                        c = c.replace(key, "z3_args['" + key + "']")
                        c = c.replace("$$$", "z3_args")
                    int_cond.append(c)
            # print(str_cond)
            # print(int_cond)

            # 筛除一些无法求解的数值条件（比如条件里的值涉及到函数调用）
            for i in int_cond.copy():
                try:
                    z3.Not(eval(i))
                except:
                    int_cond.remove(i)
            # 把字符串长度的大于小于条件转化成等于
            for i in str_cond.copy():
                if '>=' in i or '<=' in i:
                    i = re.sub('<=|>=', '==', i)
                elif '>' in i or '<' in i:
                    i = re.sub('<|>', '==', i)

            # 添加第一组全部未取反的整数、实数型条件
            int_conds = [int_cond]
            # 依次将每一个int_cond条件取反，加到条件组int_conds中
            for i in range(len(int_cond)):
                temp_conds = int_conds.copy()
                for c in temp_conds:
                    c_copy = c.copy()
                    c_copy[i] = z3.Not(eval(c[i]))
                    int_conds.append(c_copy)

            # 添加第一组全部未取反的字符串、数组型条件
            str_conds = [str_cond]
            # 依次将每一个str_cond条件取反，加到条件组str_conds中
            for i in range(len(str_cond)):
                temp_conds = str_conds.copy()
                for c in temp_conds:
                    c_copy = c.copy()
                    c_copy[i] = self.reverse_cond(c[i])
                    str_conds.append(c_copy)
            # print(str_conds)
            # print(int_conds)

            # 解析每一个条件组，替换参数执行
            res = []
            for str_c in str_conds:
                for int_c in int_conds:
                    print('约束条件：\n', str_c + int_c)
                    conds_and_params = {}
                    conds_and_params['conds'] = str_c + int_c

                    # z3符号执行求解int条件
                    solver = z3.Solver()
                    # 检查每一个条件，是字符串则eval转化，不是字符串则直接add
                    solver.reset()
                    for c in int_c:
                        if isinstance(c, str):
                            solver.add(eval(c))
                        else:
                            solver.add(c)
                    # 如果有解
                    if str(solver.check()) == 'sat':
                        ans = solver.model()
                        # print('解集：\n', ans)

                        # 如果int条件有解 继续求解str条件 替换参数
                        new_params = dict.fromkeys(args.keys())
                        # 解析条件组里的每一个条件
                        for c in str_c:
                            try:
                                # 如果条件中没有能求解的参数
                                can_solve = False
                                for pa in params_can_solve:
                                    if pa in c:
                                        can_solve = True
                                        break
                                if can_solve:
                                    # 如果是相等的条件
                                    if '==' in c:
                                        para = c.split('==')[0].strip()
                                        val = c.split('==')[1].strip()
                                        # 如果是len相关条件
                                        if 'len' in para:
                                            arg = self.find_para(para, 'len')
                                            new_params[arg] = []
                                            for i in range(int(val)):
                                                new_params[arg].append('""')
                                        # 如果是数组值相关条件
                                        elif '[' in para:
                                            arg, index = self.find_para(para, '[]')
                                            if arg in new_params.keys() and new_params[arg]:
                                                try:
                                                    new_params[arg][index] = val
                                                except:
                                                    for j in range(len(new_params[arg]), index + 1):
                                                        new_params[arg].append('""')
                                                    new_params[arg][index] = val
                                            else:
                                                new_params[arg] = []
                                                for j in range(index + 1):
                                                    new_params[arg].append('""')
                                                new_params[arg][index] = val
                                        # 如果是字符串条件
                                        else:
                                            new_params[para] = val
                                    # 如果是不等的条件
                                    elif '!=' in c:
                                        para = c.split('!=')[0].strip()
                                        val = c.split('!=')[1].strip()
                                        # 如果是len相关条件
                                        if 'len' in para:
                                            arg = self.find_para(para, 'len')
                                            new_params[arg] = []
                                            for i in range(int(val) + 1):
                                                new_params[arg].append('""')
                                        # 如果是数组值相关条件
                                        elif '[' in para:
                                            arg, index = self.find_para(para, '[]')
                                            if arg in new_params.keys() and new_params[arg]:
                                                try:
                                                    if new_params[arg][index] == '""':
                                                        if val != '""':
                                                            new_params[arg][index] = self.random_char(len(val) - 2)
                                                        else:
                                                            new_params[arg][index] = self.random_char(
                                                                random.randint(2, 5))
                                                except:
                                                    for j in range(len(new_params[arg]), index + 1):
                                                        new_params[arg].append('""')
                                                    if val != '""':
                                                        new_params[arg][index] = self.random_char(len(val) - 2)
                                                    else:
                                                        new_params[arg][index] = self.random_char(random.randint(2, 5))
                                            else:
                                                new_params[arg] = []
                                                for j in range(index + 1):
                                                    new_params[arg].append('""')
                                                if val != '""':
                                                    new_params[arg][index] = self.random_char(len(val) - 2)
                                                else:
                                                    new_params[arg][index] = self.random_char(random.randint(2, 5))
                                        # 如果是字符串条件
                                        else:
                                            # 防止前面已经有相等的条件把字符串限定
                                            if new_params[para] == '""' or new_params[para] is None:
                                                if val != '""':
                                                    new_params[para] = self.random_char(len(val) - 2)
                                                else:
                                                    new_params[para] = self.random_char(random.randint(2, 5))
                            except:
                                print(c, '约束求解错误')
                        for p in new_params.keys():
                            # 值为None一般代表是int参数
                            if not new_params[p]:
                                try:
                                    # print(p,ans[z3_args[p]])
                                    new_params[p] = ans[z3_args[p]]
                                except:
                                    # 也可能是条件求解过程中出错 生成随机参数
                                    if 'int' in args[p]:
                                        new_params[p] = self.random_value('int')
                                    elif args[p] == 'string':
                                        new_params[p] = self.random_value('string')
                                    elif args[p] == '[]string':
                                        new_params[p] = self.random_value('[]string')
                                    elif args[p] == 'real':
                                        new_params[p] = self.random_value('real')
                        # 最后把解集中所有的空字符串换成固定字符串或随机字符串
                        for p in new_params.keys():
                            if str(type(new_params[p])) == "<class 'list'>":
                                for index in range(len(new_params[p])):
                                    if new_params[p][index] == '""':
                                        new_params[p][index] = '"abc"'
                                        # new_params[p][index] = self.random_char(random.randint(2, 6))
                            elif str(type(new_params[p])) == "<class 'str'>":
                                if new_params[p] == '""':
                                    new_params[p] = '"abc"'
                                    # new_params[p] = self.random_char(random.randint(2, 6))
                        # 弥补z3的一个bug 0参数加1
                        for key in new_params.keys():
                            if str(type(new_params[key])) == "<class 'z3.z3.IntNumRef'>":
                                if new_params[key] == 0:
                                    new_params[key] = 1
                                else:
                                    # 加法
                                    if int(str(new_params[key])) > 0:
                                        new_params[key] = int(str(new_params[key])) - 1
                                    # 减法
                                    else:
                                        new_params[key] = int(str(new_params[key])) + 1
                        print('解集：\n', new_params)
                        conds_and_params['params'] = new_params
                        res.append(conds_and_params)
                    else:
                        print('无解')
                        conds_and_params['params'] = None
            print('---符号执行结束---\n')
            return res
        else:
            return None

    # 提取链码结构名
    def get_struct_name(self):
        start = self.chaincode.find('shim.Start(new(')
        # 如果没有在main函数中找到链码结构名 则在合约中找名字像链码结构体的定义
        if start == -1:
            all_struct = re.findall('type (.+?) struct', self.chaincode)
            for s in all_struct:
                if 'contract' in s.lower() or 'chaincode' in s.lower():
                    return s
        else:
            start += len('shim.Start(new(')
        end = -1
        for i in range(start, len(self.chaincode)):
            if self.chaincode[i] == ')':
                end = i
                break
        if end != -1:
            return self.chaincode[start:end]
        else:
            return None

    # 提取MockStub对象名称 即合约文件名
    def get_mockstub_name(self):
        return self.mockstub_name

    # 提取合约路径目录
    def get_path_dir(self):
        return self.path_dir

    # 提取合约包名
    def get_package_name(self):
        return self.next_word(self.chaincode, self.chaincode.find('package '))[0]

    # 通过符号执行获取init接口的参数组合  返回值：[{'conds': [约束条件], 'params': {解集}}, ...]
    def get_init_args(self):
        func_init = self.get_func_content('Init')
        if func_init and ('GetStringArgs()' in func_init or 'GetFunctionAndParameters()' in func_init):
            args = {}
            # 提取GetStringArgs()的返回值 即调用init接口的参数 为[]string类型
            if 'GetStringArgs()' in func_init:
                args[self.last_word(func_init,
                                    self.last_word(func_init, func_init.find('GetStringArgs()'))[1])[0]] = '[]string'
            # 提取GetFunctionAndParameters()的第二个返回值 即调用init接口的参数  为[]string类型
            else:
                args[self.last_word(func_init,
                                    self.last_word(func_init, func_init.find('GetFunctionAndParameters()'))[
                                        1])[0]] = '[]string'
            print('参数列表', args)
            return self.symbolic_execute(func_init, args)
        else:
            return None

    # 通过符号执行获取invoke接口的参数组合  返回值：[{'conds': [约束条件], 'params': {解集}}, ...]
    def get_invoke_args(self):
        func_invoke = self.get_func_content('Invoke')
        # 提取GetFunctionAndParameters()的第一个返回值“通过invoke接口调用的函数” 为string类型
        if func_invoke and 'GetFunctionAndParameters' in func_invoke:
            args = {}
            args[self.last_word(func_invoke, self.last_word(func_invoke, self.last_word(func_invoke, func_invoke.find(
                'GetFunctionAndParameters()'))[1])[1])[0]] = 'string'
            print('参数列表', args)
            return self.symbolic_execute(func_invoke, args)
        else:
            return None

    # 通过符号执行获取某函数的参数组合 参数：函数名  返回值：[{'conds': [约束条件], 'params': {解集}}, ...]
    def get_func_args(self, func_name):
        func_content = self.get_func_content(func_name)
        if func_content:
            # print(func_content)
            # 从函数头中提取参数列表
            args = self.get_params_list(func_content, func_name)
            print('参数列表', args)
            return self.symbolic_execute(func_content, args)
        else:
            return None

    # 根据要传的参数生成调用Init接口的代码
    def gen_mockinit(self, conds_and_params=None):
        if conds_and_params:
            code = '\t// ' + str(conds_and_params['conds']) + '\n\tres_init := stub.MockInit("1", [][]byte{'
            for key in conds_and_params['params'].keys():
                for i in conds_and_params['params'][key]:
                    if i.startswith('"'):
                        code += '[]byte(' + i + '), '
                    else:
                        code += '[]byte("' + i + '"), '
            code = code[:-2] + '})\n'
        # 如果没有参数，则无参调用Init接口
        else:
            code = '\tres_init := stub.MockInit("1", [][]byte{[]byte("")})\n'
        code += '\tif res_init.Status != 200 {\n\t\tfmt.Println("Init error!")\n\t}\n'
        return code

    # 根据要传的参数生成调用Invoke接口的代码,返回一个列表,每个元素是一个invoke调用语句和res.States的字符串
    def gen_mockinvoke(self, conds_and_params=None):
        res = []
        if conds_and_params:
            # {'conds': ['fn == "set"'], 'params': {'fn': '"set"'}}
            for key in conds_and_params['params']:
                func_name = conds_and_params['params'][key][1:-1]
                # 检查函数的返回值里是否有error，默认有
                flag_has_error_return = True
                func_head = self.get_func_head(func_name)
                if func_head:
                    if 'error)' not in func_head:
                        flag_has_error_return = False
                c_and_p = self.get_func_args(func_name)
                if c_and_p:
                    for one_cp in c_and_p:
                        code = '\t// ' + str(conds_and_params['conds']) + ' ' + str(one_cp['conds']) + '\n\tres_' + \
                               conds_and_params['params'][key][
                               1:-1] + ' := stub.MockInvoke("1", [][]byte{[]byte(' + \
                               conds_and_params['params'][key] + ')'
                        for k in one_cp['params']:
                            # 如果是数组条件 依次加入参数
                            if str(type(one_cp['params'][k])) == "<class 'list'>":
                                for arg in one_cp['params'][k]:
                                    code += ', []byte(' + arg + ')'
                            # 否则直接加入参数
                            else:
                                if str(one_cp['params'][k]).startswith('"'):
                                    code += ', []byte(' + str(one_cp['params'][k]) + ')'
                                else:
                                    code += ', []byte("' + str(one_cp['params'][k]) + '")'
                        code += '})\n\tif res_' + conds_and_params['params'][key][
                                                  1:-1] + '.Status != 200 {\n\t\tfmt.Println("Invoke ' + \
                                conds_and_params['params'][key][1:-1] + ' error!")\n\t}\n'
                        # 如果函数返回值中有error
                        if flag_has_error_return:
                            code += '\tif string(res_' + conds_and_params['params'][key][
                                                         1:-1] + '.Payload) == "" && res_' + conds_and_params['params'][
                                                                                                 key][
                                                                                             1:-1] + '.Message == "" {\n\t\tpanic("Return value error!")\n\t}\n'
                        res.append(code)
                # 如果函数不存在，或者函数无参数，或者没能从条件中提取出参数信息
                else:
                    # 如果函数返回值中有error
                    if flag_has_error_return:
                        # 给数组添加一个空字符串元素 作为参数调用
                        res.append(
                            '\t// ' + str(conds_and_params['conds']) + '\n\tres_' + conds_and_params['params'][key][
                                                                                    1:-1] + ' := stub.MockInvoke("1", [][]byte{[]byte(' + \
                            conds_and_params['params'][key] + '), []byte("")})\n\tif res_' +
                            conds_and_params['params'][
                                key][
                            1:-1] + '.Status != 200 {\n\t\tfmt.Println("Invoke ' + \
                            conds_and_params['params'][key][1:-1] + ' error!")\n\t}\n' + '\tif string(res_' +
                            conds_and_params['params'][key][
                            1:-1] + '.Payload) == "" && res_' + conds_and_params['params'][
                                                                    key][
                                                                1:-1] + '.Message == "" {\n\t\tpanic("Return value error!")\n\t}\n')
                        # 给数组添加一个随机字符串元素 作为参数调用
                        res.append(
                            '\t// ' + str(conds_and_params['conds']) + '\n\tres_' + conds_and_params['params'][key][
                                                                                    1:-1] + ' := stub.MockInvoke("1", [][]byte{[]byte(' + \
                            conds_and_params['params'][key] + '), []byte(' + self.random_char(
                                random.randint(2, 5)) + ')})\n\tif res_' + conds_and_params['params'][
                                                                               key][
                                                                           1:-1] + '.Status != 200 {\n\t\tfmt.Println("Invoke ' + \
                            conds_and_params['params'][key][1:-1] + ' error!")\n\t}\n' + '\tif string(res_' +
                            conds_and_params['params'][key][
                            1:-1] + '.Payload) == "" && res_' + conds_and_params['params'][
                                                                    key][
                                                                1:-1] + '.Message == "" {\n\t\tpanic("Return value error!")\n\t}\n')
                    else:
                        # 给数组添加一个空字符串元素 作为参数调用
                        res.append(
                            '\t// ' + str(conds_and_params['conds']) + '\n\tres_' + conds_and_params['params'][key][
                                                                                    1:-1] + ' := stub.MockInvoke("1", [][]byte{[]byte(' + \
                            conds_and_params['params'][key] + '), []byte("")})\n\tif res_' +
                            conds_and_params['params'][
                                key][
                            1:-1] + '.Status != 200 {\n\t\tfmt.Println("Invoke ' + \
                            conds_and_params['params'][key][1:-1] + ' error!")\n\t}\n')
                        # 给数组添加一个随机字符串元素 作为参数调用
                        res.append(
                            '\t// ' + str(conds_and_params['conds']) + '\n\tres_' + conds_and_params['params'][key][
                                                                                    1:-1] + ' := stub.MockInvoke("1", [][]byte{[]byte(' + \
                            conds_and_params['params'][key] + '), []byte(' + self.random_char(
                                random.randint(2, 5)) + ')})\n\tif res_' + conds_and_params['params'][
                                                                               key][
                                                                           1:-1] + '.Status != 200 {\n\t\tfmt.Println("Invoke ' + \
                            conds_and_params['params'][key][1:-1] + ' error!")\n\t}\n')
        # 如果没有参数，则不调用Invoke接口
        return res

    # 为合约写测试文件并执行
    def chaincode_symbolic_execute_test(self):
        # print([self.chaincode])
        # 备份原来的go合约
        fp = open('temp.go', 'w', encoding='utf8')
        fp.write(self.chaincode)
        fp.close()

        try:
            # 改写go合约 找到整数加减乘运算 加上整数溢出条件判断语句
            check_overflow = self.add_int_overflow_cond()

            # 生成测试文件头和测试文件尾
            test_file_head = 'package ' + self.get_package_name() + '\n\nimport (\n\t"fmt"\n\t"testing"\n\n\t"github.com/hyperledger/fabric/core/chaincode/shim"\n)\n\nfunc TestFunc(t *testing.T) {\n\tcc := new(' + self.get_struct_name() + ')\n\tstub := shim.NewMockStub("' + self.get_mockstub_name() + '", cc)\n'
            test_file_tail = '}'
            # 提取init调用语句列表
            init_codes = []
            init_args = self.get_init_args()
            if init_args:
                for cp in init_args:
                    init_codes.append(self.gen_mockinit(cp))
            else:
                init_codes.append(self.gen_mockinit())
            # 提取invoke调用语句列表嵌套列表
            invoke_codes = []
            invoke_args = self.get_invoke_args()
            if invoke_args:
                for cp in invoke_args:
                    # 每个cp为一个函数调用的约束条件和参数
                    invoke_codes.append(self.gen_mockinvoke(cp))
            # 改写go合约 加上检测有没有发生整数溢出的语句
            chaincode_list = self.chaincode.split('\n')
            for co in check_overflow:
                chaincode_list[co[0]] += co[1]
            self.chaincode = '\n'.join(chaincode_list)

            # 改写go合约 加上检测数据库的函数testdb
            self.add_testdb()
            # 改写go合约 找全局变量替换成随机值 保存到self.chaincode_random_global中
            self.replace_global_var()

            # 循环测试 生成M轮测试文件 一个测试文件执行N次
            num = 1
            for i in range(self.M):
                # 有多少种init调用语句，一轮循环就生成多少个测试文件，为每种init调用随机搭配invoke调用
                for init_code in init_codes:
                    init_and_invoke = []
                    # 随机加入每个函数的一种invoke调用语句
                    for invoke_code_list in invoke_codes:
                        init_and_invoke.append(invoke_code_list[random.randint(0, len(invoke_code_list) - 1)])
                    # 打乱顺序
                    random.shuffle(init_and_invoke)
                    # 在最前面加入init调用语句
                    init_and_invoke.insert(0, init_code)
                    test_file_init_and_invoke = ''.join(init_and_invoke)
                    # 找到所有形如[]byte("")的参数 在最后加入testdb检测数据库语句
                    testdb_args = re.findall('\[\]byte\(".*"\)', test_file_init_and_invoke)
                    test_file_testdb = '\tfmt.Println(string(stub.MockInvoke("1", [][]byte{[]byte("testdb")'
                    for arg in testdb_args:
                        test_file_testdb += ', ' + arg
                    test_file_testdb += '}).Payload))\n'
                    test_file = test_file_head + test_file_init_and_invoke + test_file_testdb + test_file_tail
                    # print(test_file)
                    # 保存的测试文件
                    fp = open(self.get_path_dir() + 'test_' + self.file_flag + '/test_file_' + str(num) + '.go', 'w')
                    fp.write(test_file)
                    fp.close()
                    # 执行N次的测试文件
                    for j in range(self.N):
                        fp = open(self.get_path_dir() + self.get_mockstub_name() + '_test.go', 'w')
                        fp.write(test_file)
                        fp.close()
                        # 执行测试
                        p = subprocess.Popen('cd ' + self.get_path_dir() + ' && wsl -e go test', shell=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = p.communicate()
                        # 保存测试结果
                        fp = open(self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(num) + '_' + str(
                            j + 1) + '.txt', 'w')
                        for line in out.splitlines():
                            fp.write(line.decode() + '\n')
                        for line in err.splitlines():
                            fp.write(line.decode() + '\n')
                        fp.close()
                    # 如果有全局变量 则替换全局变量后再执行一次
                    if self.chaincode_random_global:
                        # 把修改全局变量后 写入新的go合约
                        fp = open(self.loc, 'w')
                        fp.write(self.chaincode_random_global)
                        fp.close()
                        # 执行测试
                        p = subprocess.Popen('cd ' + self.get_path_dir() + ' && wsl -e go test', shell=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = p.communicate()
                        # 保存测试结果
                        fp = open(self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(num) + '_0.txt',
                                  'w')
                        for line in out.splitlines():
                            fp.write(line.decode() + '\n')
                        for line in err.splitlines():
                            fp.write(line.decode() + '\n')
                        fp.close()
                        # 把原合约写回
                        fp = open(self.loc, 'w')
                        fp.write(self.chaincode)
                        fp.close()
                    # 比较N次测试结果
                    fp1 = open(self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(num) + '_1.txt')
                    fp1_content = fp1.read()
                    fp1.close()
                    for j in range(1, self.N):
                        fp = open(self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(num) + '_' + str(
                            j + 1) + '.txt')
                        # 比较时去除末尾的测试执行时间
                        if fp1_content[:-8] != fp.read()[:-8]:
                            fp_err = open(
                                self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(num) + '_err.txt',
                                'w')
                            fp_err.write(self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(
                                num) + '_1.txt\n' + self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(
                                num) + '_' + str(j + 1) + '.txt\n' + 'Result not equal!\n')
                            fp_err.close()
                            fp.close()
                            break
                        fp.close()
                    # 比较替换全局变量后的测试结果
                    if self.chaincode_random_global:
                        fp = open(self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(num) + '_0.txt')
                        if fp1_content[:-8] != fp.read()[:-8]:
                            fp_err = open(
                                self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(num) + '_err.txt',
                                'a')
                            fp_err.write(self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(
                                num) + '_0.txt\n' + self.get_path_dir() + 'test_' + self.file_flag + '/test_res_' + str(
                                num) + '_1.txt\n' + 'Result not equal!\n')
                            fp_err.close()
                        fp.close()
                    num += 1
        except:
            print('Error!')
        finally:
            # 将备份在temp.go中的原合约重新写入 删除temp.go文件 删除_test.go测试文件
            fp_temp = open('temp.go')
            fp_go = open(self.loc, 'w')
            fp_go.write(fp_temp.read())
            fp_temp.close()
            fp_go.close()
            os.remove('temp.go')
            os.remove(self.get_path_dir() + self.get_mockstub_name() + '_test.go')

    # 改写go合约 加上检测数据库的函数testdb
    def add_testdb(self):
        # 将链码转化成列表形式，每行一个元素
        chaincode_list = self.chaincode.split('\n')
        # 找到Invoke函数定义的行
        row = 0
        while row < len(chaincode_list):
            invoke_row = re.search('Invoke\((.+?)shim.ChaincodeStubInterface', chaincode_list[row])
            if invoke_row:
                stub = invoke_row.group(1).strip()
                break
            row += 1
        # 找到GetFunctionAndParameters的行
        while row < len(chaincode_list):
            fn_args_row = re.search('GetFunctionAndParameters', chaincode_list[row])
            if fn_args_row:
                break
            row += 1
        # 提取fn和args
        fn_args = chaincode_list[row].split(':=')[0]
        fn = fn_args.split(',')[0].strip()
        args = fn_args.split(',')[1].strip()
        chaincode_list = chaincode_list[:row + 1] + [
            '\tif ' + fn + ' == "testdb" {\n\t\treturn shim.Success(testdb(' + stub + ', ' + args + '))\n\t}'] + chaincode_list[
                                                                                                                 row + 1:]
        chaincode_list += [
            'func testdb(stub shim.ChaincodeStubInterface, args []string) []byte {\n\tres := ""\n\tvar value []byte\n\tvar err error\n\tfor i := 0; i < len(args); i++ {\n\t\tvalue, err = stub.GetState(args[i])\n\t\tif err != nil {\n\t\t\tres += "error"\n\t\t}\n\t\tres += string(value) + ","\n\t}\n\treturn []byte(res)\n}']
        # 写入新的go合约
        self.chaincode = '\n'.join(chaincode_list)
        fp = open(self.loc, 'w')
        fp.write(self.chaincode)
        fp.close()

    # 用AST找到全局变量 替换成随机值 保存到self.chaincode_random_global中
    def replace_global_var(self):
        global_var_info = []
        # 执行CCAST.go文件获取全局变量信息
        p = subprocess.Popen('go run CCAST.go ' + self.loc[:-3] + ' Global', shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        for line in out.splitlines():
            info = line.decode()
            name = self.next_word(info, 7)[0][1:-1]
            type = self.next_word(info, 7 + len(name))[0]
            global_var_info.append({'name': name, 'type': type})
        # 如果合约中有全局变量
        if global_var_info:
            # 将合约中定义的全局变量值替换成随机值
            for gv in global_var_info:
                gv_loc = self.chaincode.find('var ' + gv['name'] + ' ' + gv['type'])
                start = -1
                end = -1
                for i in range(gv_loc + len('var ' + gv['name'] + ' ' + gv['type']), len(self.chaincode)):
                    if self.chaincode[i] == '=':
                        start = i + 2
                    elif self.chaincode[i] == '\n':
                        end = i
                        break
                if start != -1 and end != -1:
                    self.chaincode_random_global = self.chaincode.replace(
                        'var ' + gv['name'] + ' ' + gv['type'] + ' = ' + str(self.chaincode[start:end]),
                        'var ' + gv['name'] + ' ' + gv['type'] + ' = ' + self.random_value(gv['type']))
        else:
            self.chaincode_random_global = None

    # 生成随机值 参数：数据类型
    def random_value(self, num_type):
        if num_type == 'int':
            return str(random.randint(1, 100))
        if num_type == 'string':
            return self.random_char(random.randint(2, 6))
        if num_type == '[]string':
            return [self.random_char(random.randint(2, 6))] * random.randint(0, 5)
        if num_type == 'real':
            return str(random.random())

    # 获取go数值类型的最大最小长度
    def get_max_min_len(self, type_str):
        if type_str == 'uint8':
            return (255, 0)
        elif type_str == 'uint16':
            return (65535, 0)
        elif type_str == 'uint32':
            return (4294967295, 0)
        elif type_str == 'uint64':
            return (18446744073709551615, 0)
        elif type_str == 'int8':
            return (127, -128)
        elif type_str == 'int16':
            return (32767, -32768)
        elif type_str == 'int32':
            return (2147483647, -2147483648)
        elif type_str == 'int64' or type_str == 'int':
            return (9223372036854775807, -9223372036854775808)

    # 改写go合约 找到整数加减乘运算 加上条件判断语句 保存到self.chaincode中
    # 默认改写self.chaincode 也可以传入需要改写的go文件内容
    def add_int_overflow_cond(self, func_content=None):
        # 改写self.chaincode
        if not func_content:
            # 将链码转化成列表形式，每行一个元素
            chaincode_list = self.chaincode.split('\n')
            # 用于保存最近一个函数的参数列表
            args = {}
            # 用于保存需要加检测是否出现溢出的位置和语句
            check_overflow = []
            row = 0
            while row < len(chaincode_list):
                # 如果是函数定义行
                if 'func ' in chaincode_list[row]:
                    # 如果方法有接受者(xxx) 则跳过右括号的下一个单词即为函数名
                    if 'func (' in chaincode_list[row]:
                        func = self.next_word(chaincode_list[row], chaincode_list[row].find(')'))[0]
                    # 否则“func ” 后面直接跟的单词就是函数名
                    else:
                        func = self.next_word(chaincode_list[row], 0)[0]
                    # 获取函数的参数列表
                    args = self.get_params_list(chaincode_list[row], func)
                # 如果有加法 防止整数上溢
                if '+' in chaincode_list[row]:
                    try:
                        add_op_loc = chaincode_list[row].find('+')
                        left = self.last_word(chaincode_list[row], add_op_loc)[0]
                        right = self.next_word(chaincode_list[row], add_op_loc)[0]
                        max_length = self.get_max_min_len(args[left])[0]
                        # 记录语句前有多少个\t
                        t_num = 0
                        for i in chaincode_list[row]:
                            if i == '\t':
                                t_num += 1
                            else:
                                break
                        # 添加上溢的判断条件 为了让符号执行能够生成导致上溢的测试用例
                        chaincode_list[row] = '\t' * t_num + 'if ' + left + '+' + right + ' <= ' + str(
                            max_length) + ' {\n' + '\t' * t_num + chaincode_list[
                                                  row] + '\n' + '\t' * t_num + '}'
                        # 检测是否出现上溢 即两数之和是否小于其中一个数
                        check_overflow_loc = row + len(chaincode_list[row].split('\n')) - 1
                        check_overflow_code = '\n\t' * t_num + 'var_xxx := ' + left + ' + ' + right + '\n' + '\t' * t_num + 'if var_xxx < ' + left + ' || var_xxx < ' + right + ' {\n' + '\t' * (
                            t_num + 1) + 'panic("' + args[
                                                  left] + ' overflow in function ' + func + '")\n' + '\t' * t_num + '}'
                        check_overflow.append((check_overflow_loc, check_overflow_code))
                    except:
                        pass
                # 如果有减法 防止整数下溢
                elif '-' in chaincode_list[row]:
                    try:
                        add_op_loc = chaincode_list[row].find('-')
                        left = self.last_word(chaincode_list[row], add_op_loc)[0]
                        right = self.next_word(chaincode_list[row], add_op_loc)[0]
                        min_length = self.get_max_min_len(args[left])[1]
                        # 记录语句前有多少个\t
                        t_num = 0
                        for i in chaincode_list[row]:
                            if i == '\t':
                                t_num += 1
                            else:
                                break
                        # 添加下溢的判断条件 为了让符号执行能够生成导致上溢的测试用例
                        chaincode_list[row] = '\t' * t_num + 'if ' + left + '-' + right + ' >= ' + str(
                            min_length) + ' {\n' + '\t' * t_num + chaincode_list[
                                                  row] + '\n' + '\t' * t_num + '}'
                        # 检测是否出现下溢 即两数之差是否小于被减数
                        check_overflow_loc = row + len(chaincode_list[row].split('\n')) - 1
                        check_overflow_code = '\n\t' * t_num + 'var_xxx := ' + left + ' - ' + right + '\n' + '\t' * t_num + 'if var_xxx > ' + left + ' {\n' + '\t' * (
                            t_num + 1) + 'panic("' + args[
                                                  left] + ' overflow in function ' + func + '")\n' + '\t' * t_num + '}'
                        check_overflow.append((check_overflow_loc, check_overflow_code))
                    except:
                        pass
                row += 1
            # 写入新的go合约
            self.chaincode = '\n'.join(chaincode_list)
            # print(self.chaincode)
            return check_overflow
        # 改写传入的go文件内容
        else:
            # 将代码转化成列表形式，每行一个元素
            chaincode_list = func_content.split('\n')
            # 用于保存最近一个函数的参数列表
            args = {}
            # 用于保存需要加检测是否出现溢出的位置和语句
            check_overflow = []
            row = 0
            while row < len(chaincode_list):
                # 如果是函数定义行
                if 'func ' in chaincode_list[row]:
                    if 'func (' in chaincode_list[row]:
                        func = self.next_word(chaincode_list[row], chaincode_list[row].find(')'))[0]
                    else:
                        func = self.next_word(chaincode_list[row], 0)[0]
                    args = self.get_params_list(chaincode_list[row], func)
                # 如果有加法 防止整数上溢
                if '+' in chaincode_list[row]:
                    try:
                        add_op_loc = chaincode_list[row].find('+')
                        left = self.last_word(chaincode_list[row], add_op_loc)[0]
                        right = self.next_word(chaincode_list[row], add_op_loc)[0]
                        max_length = self.get_max_min_len(args[left])[0]
                        # 记录语句前有多少个\t
                        t_num = 0
                        for i in chaincode_list[row]:
                            if i == '\t':
                                t_num += 1
                            else:
                                break
                        # 添加上溢的判断条件 为了让符号执行能够生成导致上溢的测试用例
                        chaincode_list[row] = '\t' * t_num + 'if ' + left + '+' + right + ' <= ' + str(
                            max_length) + ' {\n' + '\t' * t_num + chaincode_list[
                                                  row] + '\n' + '\t' * t_num + '}'
                        # 检测是否出现上溢 即两数之和是否小于其中一个数
                        check_overflow_loc = row + len(chaincode_list[row].split('\n')) - 1
                        check_overflow_code = '\n\t' * t_num + 'var_xxx := ' + left + ' + ' + right + '\n' + '\t' * t_num + 'if var_xxx < ' + left + ' || var_xxx < ' + right + ' {\n' + '\t' * (
                            t_num + 1) + 'panic("' + args[
                                                  left] + ' overflow in function ' + func + '")\n' + '\t' * t_num + '}'
                        check_overflow.append((check_overflow_loc, check_overflow_code))
                    except:
                        pass
                # 如果有减法 防止整数下溢
                elif '-' in chaincode_list[row]:
                    try:
                        add_op_loc = chaincode_list[row].find('-')
                        left = self.last_word(chaincode_list[row], add_op_loc)[0]
                        right = self.next_word(chaincode_list[row], add_op_loc)[0]
                        min_length = self.get_max_min_len(args[left])[1]
                        # 记录语句前有多少个\t
                        t_num = 0
                        for i in chaincode_list[row]:
                            if i == '\t':
                                t_num += 1
                            else:
                                break
                        # 添加下溢的判断条件 为了让符号执行能够生成导致上溢的测试用例
                        chaincode_list[row] = '\t' * t_num + 'if ' + left + '-' + right + ' >= ' + str(
                            min_length) + ' {\n' + '\t' * t_num + chaincode_list[
                                                  row] + '\n' + '\t' * t_num + '}'
                        # 检测是否出现下溢 即两数之差是否小于被减数
                        check_overflow_loc = row + len(chaincode_list[row].split('\n')) - 1
                        check_overflow_code = '\n\t' * t_num + 'var_xxx := ' + left + ' - ' + right + '\n' + '\t' * t_num + 'if var_xxx > ' + left + ' {\n' + '\t' * (
                            t_num + 1) + 'panic("' + args[
                                                  left] + ' overflow in function ' + func + '")\n' + '\t' * t_num + '}'
                        check_overflow.append((check_overflow_loc, check_overflow_code))
                    except:
                        pass
                row += 1
            # 写入新的go文件
            func_content = '\n'.join(chaincode_list)
            return func_content, check_overflow

    # 对普通函数进行符号执行检测 普通go错误也能检测出来
    def normal_func_symbolic_execute_test(self):
        # 执行CCAST.go文件获取导入包的信息
        p = subprocess.Popen('go run CCAST.go ' + self.loc[:-3] + ' Import', shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        imports = []
        for line in out.splitlines():
            imports.append(line.decode())

        funcs = re.findall('func (.+?)\(', self.chaincode)
        for func_name in funcs:
            # 去除链码方法、main函数、可以通过Invoke调用的函数
            if self.get_struct_name() in func_name or func_name == 'main' or func_name in self.get_func_content(
                    'Invoke'):
                continue
            # 获取函数主体
            func_content = self.get_func_content(func_name)
            # 从函数头中提取参数列表
            args = self.get_params_list(func_content, func_name)
            # 有参数
            have_args = True
            if args:
                # 找到整数加减乘运算 加上整数溢出条件判断语句
                func_content, check_overflow = self.add_int_overflow_cond(func_content)
                # 获取对该函数符号执行的约束条件和解集
                conds_and_params = self.symbolic_execute(func_content, args)

                # 加上检测有没有发生整数溢出的语句
                chaincode_list = func_content.split('\n')
                for co in check_overflow:
                    chaincode_list[co[0]] += co[1]
                func_content = '\n'.join(chaincode_list)

                # 用于保存该函数的测试结果
                fp_res = open(self.get_path_dir() + 'test_' + self.file_flag + '/' + func_name + '_functest_res.txt',
                              'w')
                # 替换参数符号执行
                if conds_and_params:
                    # 记录测试文件内容
                    file_content = 'package main\n\nimport (\n'
                    # 只保留该函数中用到的包
                    for imp in imports:
                        if imp.split('/')[-1][:-1] in func_content or imp[1:-1] in func_content:
                            file_content += '\t' + imp + '\n'
                    # 将待测函数和main函数写入go文件
                    file_content += ')\n\n' + func_content + '\n\nfunc main() {\n\t' + func_name + '('
                    # 用xxx记录参数的位置 便于后面替换
                    for i in range(len(args)):
                        file_content += 'xxx, '
                    file_content = file_content[:-2] + ')\n}'
                    times = 1
                    for cp in conds_and_params:
                        repl_params = func_name + '('
                        for key in cp['params']:
                            repl_params += str(cp['params'][key]) + ', '
                        if len(cp['params']) < 1:
                            file_content = re.sub('\t' + func_name + '\(.*\)', '\t' + repl_params + ')',
                                                  file_content)
                        else:
                            file_content = re.sub('\t' + func_name + '\(.*\)', '\t' + repl_params[:-2] + ')',
                                                  file_content)
                        # print(file_content)
                        # 写一个单独测试这个函数的go文件
                        fp = open(self.get_path_dir() + 'test_' + self.file_flag + '/' + func_name + '_functest_' + str(
                            times) + '.go', 'w')
                        fp.write(file_content)
                        fp.close()
                        print('运行结果：')
                        fp_res.write('----- ' + func_name + '_functest_' + str(times) + '.go -----\n')
                        # 执行测试
                        p = subprocess.Popen(
                            'cd ' + self.get_path_dir() + 'test_' + self.file_flag + ' && go run ' + func_name + '_functest_' + str(
                                times) + '.go', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = p.communicate()
                        for line in out.splitlines():
                            print(line.decode())
                            fp_res.write(line.decode() + '\n')
                        for line in err.splitlines():
                            print(line.decode())
                            fp_res.write(line.decode() + '\n')
                        fp_res.write('\n')
                        times += 1
                    fp_res.close()
                else:
                    have_args = False
            else:
                have_args = False
            # 如果无参数 直接执行一次
            if not have_args:
                # 记录文件内容
                file_content = 'package main\n\nimport (\n'
                # 只保留该函数中用到的包
                for imp in imports:
                    if imp.split('/')[-1][:-1] in func_content:
                        file_content += '\t' + imp + '\n'
                # 将待测函数和main函数写入go文件
                file_content += ')\n\n' + func_content + '\n\nfunc main() {\n\t' + func_name + '()\n}'
                # 写一个单独测试这个函数的go文件
                fp = open(self.get_path_dir() + 'test_' + self.file_flag + '/' + func_name + '_functest.go', 'w')
                fp.write(file_content)
                fp.close()
                # 用于保存该函数的测试结果
                fp_res = open(self.get_path_dir() + 'test_' + self.file_flag + '/' + func_name + '_functest_res.txt',
                              'w')
                fp_res.write('----- ' + func_name + '_functest.go -----\n')
                # 执行测试
                p = subprocess.Popen(
                    'cd ' + self.get_path_dir() + 'test_' + self.file_flag + ' && go run ' + func_name + '_functest.go',
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                for line in out.splitlines():
                    fp_res.write(line.decode() + '\n')
                for line in err.splitlines():
                    fp_res.write(line.decode() + '\n')
                fp_res.close()


if __name__ == '__main__':
    ccse = CCSE('chaincodes/sacc/sacc.go', 5, 2)
    ccse.normal_func_symbolic_execute_test()
    ccse.chaincode_symbolic_execute_test()
