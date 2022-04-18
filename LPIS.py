from dataclasses import InitVar
from mimetypes import init
from lark import Discard
from lark import Lark,Token,Tree
from lark.tree import pydot__tree_to_png
from lark.visitors import Interpreter

class MyInterpreter (Interpreter):
    def __init__(self):
        self.output = {}
        self.warnings = {}
        self.errors = {}
        self.correct = True
        self.inCicle = False
        self.if_count = 0
        self.if_depth = {}
        self.nivel_if = 0
        self.instructions = {}
        self.controlID = 0
        self.controlStructs = {}

        self.if_parts = {}
        self.code = ""
        self.html_body = ""

        self.atomic_vars = dict()
        # ATOMIC_VARS = {VARNAME : (TYPE,VALUE,INIT?,USED?)}

        self.struct_vars = dict()
        # STRUCT_VARS = {VARNAME : (TYPE,SIZE,VALUE,USED?)}

        self.nrStructs = dict()

        self.TAG = "-=ANALYZER=-"

    def start(self,tree):
        print(self.TAG + "\n\tSTART")
        self.code += "-{\n"
        self.html_body += "<pre><body>\n<p class=\"code\">\n-{\n</p>\n"
        self.visit(tree.children[1])
        self.html_body += "<p class=\"code\">\n}-\n</p>\n"
        self.code += "}-\n"
        print(self.TAG + "\n\tFINISH")
        
        for var in self.atomic_vars.keys():
            if var not in self.warnings.keys():
                    self.warnings[var] = []

            if self.atomic_vars[var][2] == 0 and self.atomic_vars[var][3] == 0:
                self.warnings[var].append("Variable \"" + var + "\" was never initialized nor used.")

            elif self.atomic_vars[var][2] == 1 and self.atomic_vars[var][3] == 0:
                self.warnings[var].append("Variable \"" + var + "\" was never used.")

        for var in self.struct_vars.keys():
            if var not in self.warnings.keys():
                    self.warnings[var] = []

            if self.struct_vars[var][0] not in self.nrStructs.keys():
                self.nrStructs[self.struct_vars[var][0]] = 1
            
            else:
                self.nrStructs[self.struct_vars[var][0]] += 1

            if self.struct_vars[var][3] == 0:
                self.warnings[var].append("Variable \"" + var + "\" was never used.")


        print("a -> " + str(self.atomic_vars['a']))

        self.output["atomic_vars"] = self.atomic_vars
        self.output["struct_vars"] = self.struct_vars
        self.output["correct"] = self.correct
        self.output["errors"] = self.errors
        self.output["warnings"] = self.warnings
        self.output["if_count"] = self.if_count
        self.output["if_depth"] = self.if_depth
        self.output["nrStructs"] = self.nrStructs
        self.output["instructions"] = self.instructions
        self.output["controlStructs"] = self.controlStructs
        self.output["if_parts"] = self.if_parts
        self.output["code"] = self.code
        self.output["html_body"] = self.html_body

        return self.output

    def program(self, tree):
        for c in tree.children:
            self.visit(c)

        pass

    def instruction(self,tree):
        self.visit(tree.children[0])

        pass

    def comment(self, tree):
        comment = tree.children[0].value
        self.code += comment + "\n"
        self.html_body += "<p class=\"comment\">\n" + comment + "\n</p>\n"
        #print("\t-=AUTHOR'S COMMENT=-\n\t\t" + comment[2:(len(comment)-2)])

        pass

    def declaration(self, tree):
        self.visit(tree.children[0])

        pass

    def atomic(self, tree):
        if "atomic_declaration" not in self.instructions.keys():
            self.instructions["atomic_declaration"] = 1
        else:
            self.instructions["atomic_declaration"] += 1

        var_type = tree.children[0].value        

        var_name = tree.children[1].value

        if var_name not in self.errors.keys():
            self.errors[var_name] = set()
        
        self.html_body += "<p class=\"code\">\n"

        flag = False

        if(var_name in self.atomic_vars.keys() or var_name in self.struct_vars.keys()):
            self.correct = False
            self.errors[var_name].add("Variable \"" + var_name + "\" declared more than once!")
            self.html_body += "<div class=\"error\">"+var_type + " " + var_name
            flag = True

        self.code += var_type + " " + var_name
        if not flag:
            self.html_body += var_type + " " + var_name

        var_value = None
        if flag == True:
            var_value = self.atomic_vars[var_name][1]
        init = 0
        used = 0

        if(len(tree.children) > 3):
            self.code += " = " 
            self.html_body += " = "
            var_value = self.visit(tree.children[3])
            print("RETORNA => " + str(var_value))
            init = 1
            if "atrib" not in self.instructions.keys():
                self.instructions["atrib"] = 1
            else:
                self.instructions["atrib"] += 1


        val = (var_type,var_value,init,used)
        self.atomic_vars[var_name] = val

        if flag:
            self.html_body += "<span class=\"errortext\">Variable declared more than once!</span></div>"

        flag = False

        self.code += ";\n"
        self.html_body += ";\n</p>\n"

        pass

    def elem(self, tree):

        if(not isinstance(tree.children[0], Tree)):
            if(tree.children[0].type == "ESCAPED_STRING"):
                self.code += str(tree.children[0])
                self.html_body += str(tree.children[0])
                return str(tree.children[0].value[1:(len(tree.children[0].value)-1)])
            elif(tree.children[0].type == "DECIMAL"):
                self.code += str(tree.children[0])
                self.html_body += str(tree.children[0])
                return float(tree.children[0].value)
            elif(tree.children[0].type == "SIGNED_INT"):
                self.code += str(tree.children[0])
                self.html_body += str(tree.children[0])
                return int(tree.children[0].value)
        else:
            r = self.visit(tree.children[0])
            return r

    def structure(self, tree):
        if "structure_declaration" not in self.instructions.keys():
            self.instructions["structure_declaration"] = 1
        else:
            self.instructions["structure_declaration"] += 1

        self.visit(tree.children[0])

        pass
 
    def set(self, tree):
        self.html_body += "<p class=\"code\">\n"
        ret = set()
        childs = len(tree.children)
        sizeS = 0
        self.code += "set " + tree.children[0].value
        self.html_body += "set " + tree.children[0].value
        print(tree.pretty())
        if childs != 1 and childs != 4:
            self.code += " = "
            self.html_body += " = "
            for c in tree.children[2:]:
                if c != "{" and c != "}" and c != ",":
                    ret.add(self.visit(c))
                if c == "{" or c == "}" or c == ",":
                    self.code += c.value
                    self.html_body += c.value
                    if c == ",":
                        self.code += " "
                        self.html_body += " "
            #print("Set \"" + tree.children[0] + "\" => " + str(ret))
            sizeS = len(ret)            
        elif childs == 4:
            self.code += " = {}"
            self.html_body += " = {}"
        self.code += ";\n"
        self.html_body += ";\n</p>\n"
        self.struct_vars[tree.children[0].value] = ("set", sizeS, ret, 0)


        pass

    def list(self, tree):
        self.html_body += "<p class=\"code\">\n"

        ret = list()
        childs = len(tree.children)
        sizeL = 0
        self.code += "list " + tree.children[0].value
        self.html_body += "list " + tree.children[0].value

        if childs != 1 and childs != 4:
            self.code += " = "
            self.html_body += " = "
            for c in tree.children[2:]:
                if c != "[" and c != "]" and c != ",":
                    ret.append(self.visit(c))
                if c == "[" or c == "]" or c == ",":
                    self.code += c.value
                    self.html_body += c.value
                    if c == ",":
                        self.code += " "
                        self.html_body += " "
            #print("List \"" + tree.children[0] + "\" => " + str(ret))
            sizeL = len(ret)
        elif childs == 4:
            self.code += " = []"
            self.html_body += " = []"

        self.code += ";\n"
        self.html_body += ";\n</p>\n"

        self.struct_vars[tree.children[0].value] = ("list", sizeL, ret, 0)

        pass

    def tuple(self, tree):
        self.html_body += "<p class=\"code\">\n"
        aux = list()
        ret = tuple()
        sizeT = 0
        childs = len(tree.children)
        self.code += "tuple " + tree.children[0].value
        self.html_body += "tuple " + tree.children[0].value
        if childs != 1 and childs != 4:
            self.code += " = "
            self.html_body += " = "
            for c in tree.children[2:]:
                if c != "(" and c != ")" and c != ",":
                    aux.append(self.visit(c))
                if c == "(" or c == ")" or c == ",":
                    self.code += c.value
                    self.html_body += c.value
                    if c == ",":
                        self.code += " "
                        self.html_body += " "
            ret = tuple(aux)
            #print("Tuple \"" + tree.children[0] + "\" => " + str(ret))
            sizeT = len(ret)
        elif childs == 4:
            self.code += " = ()"
            self.html_body += " = ()"

        self.code += ";\n"
        self.html_body += ";\n</p>\n"

        self.struct_vars[tree.children[0].value] = ("tuple", sizeT, ret, 0)

        pass

    def dict(self, tree):
        self.html_body += "<p class=\"code\">\n"

        ret = dict()
        childs = len(tree.children)
        sizeD = 0
        self.code += "dict " + tree.children[0].value
        self.html_body += "dict " + tree.children[0].value
        if childs != 1 and childs != 4:
            self.code += " = {"
            self.html_body += " = {"
            start = 3
            while start < childs-1:
                key = self.visit(tree.children[start])
                self.code += " : "
                self.html_body += " : "
                value = self.visit(tree.children[start+2])
                if start + 4 < (childs-1):
                    self.code += ", "
                    self.html_body += ", "
                ret[key] = value 
                start += 4
            #print("Dict \"" + tree.children[0] + "\" => " + str(ret))
            self.code += "}"
            self.html_body += "}"
            sizeD = len(ret)
        elif childs == 4:
            self.code += " = {}"
            self.html_body += " = {}"

        self.code += ";\n"
        self.html_body += ";\n</p>\n"
        
        self.struct_vars[tree.children[0].value] = ("dict", sizeD, ret, 0)

        pass

    def atrib(self,tree):

        if "atrib" not in self.instructions.keys():
            self.instructions["atrib"] = 1
        else:
            self.instructions["atrib"] += 1

        self.html_body += "<p class=\"code\">\n"

        self.code += tree.children[0].value + " = "

        if str(tree.children[0]) not in self.errors.keys():
            self.errors[str(tree.children[0])] = set()

        if str(tree.children[0]) not in self.atomic_vars.keys():
            self.errors[str(tree.children[0])].add("Variable \"" + tree.children[0] + "\" was not declared")
            self.correct = False
            typeV = "undefined"
            valueV = None
            self.html_body += "<div class=\"error\">" + tree.children[0].value + " = "
            valueV = self.visit(tree.children[2])
            self.html_body += "<span class=\"errortext\">Variable undeclared</span></div>"
            self.atomic_vars[str(tree.children[0])] = tuple([typeV,valueV,0,1])

        else:
            typeV = self.atomic_vars[str(tree.children[0])][0]
            self.html_body += tree.children[0].value + " = "
            valueV = self.visit(tree.children[2])
            self.atomic_vars[str(tree.children[0])] = tuple([typeV,valueV,1,1])

        self.html_body += ";\n</p>\n"
        self.code += ";\n"
            
        pass

    def initcicle(self, tree):
        if "atrib" not in self.instructions.keys():
            self.instructions["atrib"] = 1
        else:
            self.instructions["atrib"] += 1

        self.code += tree.children[0].value + " = "
        


        if str(tree.children[0]) not in self.errors.keys():
            self.errors[str(tree.children[0])] = set()
        if str(tree.children[0]) not in self.atomic_vars.keys():
            self.errors[str(tree.children[0])].add("Variable \"" + tree.children[0] + "\" was not declared")
            self.html_body += "<div class=\"error\">"+tree.children[0].value + " = "
            valueV = self.visit(tree.children[2])
            self.html_body += "<span class=\"errortext\">Variable was not declared</span></div>"
            self.correct = False
        else:
            typeV = self.atomic_vars[tree.children[0]][0]
            self.html_body += tree.children[0].value + " = "
            valueV = self.visit(tree.children[2])
            self.atomic_vars[str(tree.children[0])] = tuple([typeV,valueV,1,1])

        pass

    def print(self,tree):
        if "print" not in self.instructions.keys():
            self.instructions["print"] = 1
        else:
            self.instructions["print"] += 1

        self.html_body += "<p class=\"code\">\nprint("

        self.code += "print("

        if tree.children[1].type == "VARNAME":
            self.code += tree.children[1].value
            if str(tree.children[1]) not in self.errors.keys():
                self.errors[str(tree.children[1])] = set()
            if str(tree.children[1]) not in self.atomic_vars.keys():
                self.errors[str(tree.children[1])].add("Variable \"" + tree.children[1] + "\" was not declared")
                self.html_body += "<div class=\"error\">" + tree.children[0].value + "<span class=\"errortext\">Variable undeclared</span></div>"
                self.correct = False
            elif not self.atomic_vars[str(tree.children[1])][2]:
                self.errors[str(tree.children[1])].add("Variable \"" + tree.children[1] + "\" declared but not initialized")
                self.html_body += "<div class=\"error\">" + tree.children[0].value + "<span class=\"errortext\">Variable was never initialized</span></div>"
                self.correct = False
            else:
                print("> " + str(self.atomic_vars[tree.children[1]][1]))
                self.html_body += tree.children[1].value
            
        elif tree.children[1].type == "ESCAPED_STRING":
            self.code += tree.children[1].value
            self.html_body += tree.children[1].value
            s = tree.children[1]
            s = s.replace("\"","")
            print("> " + s)
        
        self.code += ");\n"
        self.html_body += ");\n</p>\n"
            
        pass

    def read(self,tree):
        if "read" not in self.instructions.keys():
            self.instructions["read"] = 1
        else:
            self.instructions["read"] += 1

        self.code += "read(" + tree.children[1].value + ");\n"
        self.html_body += "<p class=\"code\">\nread("

        if str(tree.children[1]) not in self.errors.keys():
            self.errors[str(tree.children[1])] = set()

        if str(tree.children[1]) not in self.atomic_vars.keys():
            if str(tree.children[1]) in self.struct_vars.keys():
                self.errors[str(tree.children[1])].add("Variable \"" + tree.children[1] + "\" cannot be defined by user input.")
                self.html_body += "<div class=\"error\">" + tree.children[0].value + "<span class=\"errortext\">Variable is a structure</span></div>"
            else:
                self.errors[str(tree.children[1])].add("Variable \"" + tree.children[1] + "\" was not declared")
                self.html_body += "<div class=\"error\">" + tree.children[0].value + "<span class=\"errortext\">Variable undeclared</span></div>"
            self.correct = False
        
        else:
            self.html_body += tree.children[1].value
            value = input("> ")
            typeV = self.atomic_vars[tree.children[1]][0]
            initV = 1
            usedV = 1
            val = int(value)
            self.atomic_vars[tree.children[1]] = tuple([typeV, val, initV, usedV])

        self.code += ");\n"        
        self.html_body += ");\n</p>\n"

        pass

    def cond(self,tree):
        if "if" not in self.instructions.keys():
            self.instructions["if"] = 1
        else:
            self.instructions["if"] += 1

        self.html_body += "<p class=\"code\">\n"


        # Vamos buscar todas as estruturas que estão ativas (ainda nao foram fechadas) e consideramos que a estrutura está aninhada dentro delas
        parents = []
        for id in self.controlStructs.keys():
            if self.controlStructs[id][1] == 1:
                parents.append(id)

        # Pomos no dict um tuplo com o tipo da estrutura de controlo, uma flag que nos diz que está ativa e a lista das estruturas de hierarquia superior 
        self.controlStructs[(self.controlID)] = tuple(["if",1,parents])
        # Incrementamos o ID para a proxima estrutura de controlo
        self.controlID += 1

        # Usamos o contador de ifs para definir os ids das estruturas de controlo
        self.if_count += 1
        self.if_depth[self.if_count] = self.nivel_if

        self.if_parts[self.if_count] = (tree.children[2],tree.children[4])

        l = len(tree.children)

        self.code += "if("
        self.html_body += "if("
        self.visit(tree.children[2])
        self.code += ")"
        self.html_body += ")"

        self.visit(tree.children[4])     

        if(tree.children[(l-2)] == "else"):
            self.code += " else "
            self.html_body += " else "
            self.visit(tree.children[(l-1)])

        pass

    def ciclewhile(self,tree):
        if "while" not in self.instructions.keys():
            self.instructions["while"] = 1
        else:
            self.instructions["while"] += 1

        self.html_body += "<p class=\"code\">\n"

        # Vamos buscar todas as estruturas que estão ativas (ainda nao foram fechadas) e consideramos que a estrutura está aninhada dentro delas
        parents = []
        for id in self.controlStructs.keys():
            if self.controlStructs[id][1] == 1:
                parents.append(id)

        # Pomos no dict um tuplo com o tipo da estrutura de controlo, uma flag que nos diz que está ativa e a lista das estruturas de hierarquia superior 
        self.controlStructs[self.controlID] = tuple(["while",1,parents])
        # Incrementamos o ID para a proxima estrutura de controlo
        self.controlID += 1

        aux = self.nivel_if 
        self.nivel_if = 0
        self.inCicle = True

        self.code += "while("
        self.html_body += "while("

        self.visit(tree.children[2])

        self.code += ")"
        self.html_body += ")"

        self.visit(tree.children[4])
        
        self.inCicle = False
        self.nivel_if = aux

        pass

    def ciclefor(self,tree):
        if "for" not in self.instructions.keys():
            self.instructions["for"] = 1
        else:
            self.instructions["for"] += 1

        # Vamos buscar todas as estruturas que estão ativas (ainda nao foram fechadas) e consideramos que a estrutura está aninhada dentro delas
        parents = []
        for id in self.controlStructs.keys():
            if self.controlStructs[id][1] == 1:
                parents.append(id)

        # Pomos no dict um tuplo com o tipo da estrutura de controlo, uma flag que nos diz que está ativa e a lista das estruturas de hierarquia superior 
        self.controlStructs[self.controlID] = tuple(["for",1,parents])
        # Incrementamos o ID para a proxima estrutura de controlo
        self.controlID += 1

        aux = self.nivel_if 
        self.nivel_if = 0
        self.inCicle = True

        self.html_body += "<p class=\"code\">\n"

        for c in tree.children:
            if c != "for" and c != "(" and c != ")" and c != ";" and c != ",":
                self.visit(c)
            if c == "for" or c == "(" or c == ")" or c == ";" or c == ",":
                self.code += c.value
                self.html_body += c.value
                if(c == ";" or c == ","):
                    self.code += " "
                    self.html_body += " "
        
        self.inCicle = False
        self.nivel_if = aux

        pass

    def inc(self, tree):
        self.code += tree.children[0] + "++"
        self.html_body += tree.children[0] + "++"
        typeV = self.atomic_vars[str(tree.children[0])][0]
        valueV = self.atomic_vars[str(tree.children[0])][1] + 1
        self.atomic_vars[str(tree.children[0])] = tuple([typeV,valueV,1,1])
        
        pass

    def dec(self, tree):
        self.code += tree.children[0] + "--"
        self.html_body += tree.children[0] + "--"
        typeV = self.atomic_vars[str(tree.children[0])][0]
        valueV = self.atomic_vars[str(tree.children[0])][1] - 1
        self.atomic_vars[str(tree.children[0])] = tuple([typeV,valueV,1,1])

        pass

    def ciclerepeat(self,tree):
        if "repeat" not in self.instructions.keys():
            self.instructions["repeat"] = 1
        else:
            self.instructions["repeat"] += 1

        # Vamos buscar todas as estruturas que estão ativas (ainda nao foram fechadas) e consideramos que a estrutura está aninhada dentro delas
        parents = []
        for id in self.controlStructs.keys():
            if self.controlStructs[id][1] == 1:
                parents.append(id)

        # Pomos no dict um tuplo com o tipo da estrutura de controlo, uma flag que nos diz que está ativa e a lista das estruturas de hierarquia superior 
        self.controlStructs[self.controlID] = tuple(["repeat",1,parents])
        # Incrementamos o ID para a proxima estrutura de controlo
        self.controlID += 1

        aux = self.nivel_if 
        self.nivel_if = 0
        self.inCicle = True
        
        print(tree.children)

        self.code += "repeat(" + tree.children[2] + ")"
        self.html_body += "<p class=\"code\">\nrepeat(" + tree.children[2].value + ")"

        self.visit(tree.children[4])
        
        self.inCicle = False
        self.nivel_if = aux

        pass

    def body(self,tree):
        self.visit_children(tree)

        pass

    def open(self,tree):
        if not self.inCicle:
            self.nivel_if += 1
        self.code += "{\n"
        self.html_body += "{\n</p>\n"

        pass

    def close(self,tree):
        self.nivel_if -= 1

        newDict = dict(filter(lambda elem: elem[1][1] == 1, self.controlStructs.items()))

        k = max(newDict.keys())
        self.controlStructs[k] = (self.controlStructs[k][0],0,self.controlStructs[k][2])

        self.code += "}\n"
        self.html_body += "<p class=\"code\">\n}\n</p>\n"
        pass

    def op(self,tree):
        if(len(tree.children) > 1):
            if(tree.children[0] == "!"):
                self.code += "!"
                self.html_body += "!"
                r = int(self.visit(tree.children[1]))
                if r == 0: r = 1
                else: r = 0
            elif(tree.children[1] == "&"):
                t1 = self.visit(tree.children[0])
                self.code += " & "
                self.html_body += " & "
                t2 = self.visit(tree.children[2])
                if t1 and t2:
                    r = 1
                else:
                    r = 0
            elif(tree.children[1] == "#"):
                t1 = self.visit(tree.children[0])
                self.code += " # "
                self.html_body += " # "
                t2 = self.visit(tree.children[2])
                if t1 or t2:
                    r = 1
                else:
                    r = 0
        else:
            r = self.visit(tree.children[0])

        return r

    def factcond(self,tree):
        if len(tree.children) > 1:
            t1 = self.visit(tree.children[0])
            self.code += " " + tree.children[1].value + " "
            self.html_body += " " + tree.children[1].value + " "
            t2 = self.visit(tree.children[2])
            if tree.children[1] == "<=":
                if t1 <= t2:
                    r = 1
                else:
                    r = 0
            elif tree.children[1] == "<":
                if t1 < t2:
                    r = 1
                else:
                    r = 0
            elif tree.children[1] == ">=":
                if t1 >= t2:
                    r = 1
                else:
                    r = 0
            elif tree.children[1] == ">":
                if t1 > t2:
                    r = 1
                else:
                    r = 0
            elif tree.children[1] == "==":
                if t1 == t2:
                    r = 1
                else:
                    r = 0
            elif tree.children[1] == "!=":
                if t1 != t2:
                    r = 1
                else:
                    r = 0
        else:
            r = self.visit(tree.children[0])
        
        return r

    def expcond(self,tree):
        if len(tree.children) > 1:
            t1 = self.visit(tree.children[0])
            self.code += " " + tree.children[1].value + " "
            self.html_body += " " + tree.children[1].value + " "
            t2 = self.visit(tree.children[2])
            if(tree.children[1] == "+"):
                r = t1 + t2
            elif(tree.children[1] == "-"):
                r = t1 - t2
        else:
            r = self.visit(tree.children[0])

        return r

    def termocond(self,tree):
        if len(tree.children) > 1:
            t1 = self.visit(tree.children[0])
            self.code += " " + tree.children[1].value + " "
            self.html_body += " " + tree.children[1].value + " "
            t2 = self.visit(tree.children[2])
            if(tree.children[1] == "*"):
                r = t1 * t2
            elif(tree.children[1] == "/"):
                r = int(t1 / t2)
            elif(tree.children[1] == "%"):
                r = t1 % t2
        else:
            r = self.visit(tree.children[0])

        return r

    def factor(self,tree):
        r = None
        if tree.children[0].type == 'SIGNED_INT':
            r = int(tree.children[0])
            self.code += str(r)
            self.html_body += str(r)
        elif tree.children[0].type == 'VARNAME':

            if str(tree.children[0]) not in self.errors.keys():
                self.erros[str(tree.children[0])] = set()

            if str(tree.children[0]) not in self.atomic_vars.keys():
                self.errors[str(tree.children[0])].add("Undeclared variable \"" + str(tree.children[0]) + "\"")
                self.correct = False
                self.html_body += "<div class=\"error\">"+tree.children[0].value+"<span class=\"errortext\">Undeclared Variable</span></div>"
                r = -1
            elif self.atomic_vars[str(tree.children[0])][2] == 0:
                print(tree.children[0].value + " -> " + str(self.atomic_vars[str(tree.children[0])]))
                self.errors[str(tree.children[0])].add("Variable \"" + str(tree.children[0]) + "\" was never initialized")
                self.html_body += "<div class=\"error\">"+tree.children[0].value+"<span class=\"errortext\">Variable was never initialized</span></div>"
                self.correct = False
                r = self.atomic_vars[str(tree.children[0])][1]
                typeV = self.atomic_vars[str(tree.children[0])][0]
                initV = self.atomic_vars[str(tree.children[0])][2]
                self.atomic_vars[str(tree.children[0])] = tuple([typeV,r,initV,1])
            else:
                r = self.atomic_vars[str(tree.children[0])][1]
                typeV = self.atomic_vars[str(tree.children[0])][0]
                initV = self.atomic_vars[str(tree.children[0])][2]
                self.html_body += tree.children[0].value
                self.atomic_vars[str(tree.children[0])] = tuple([typeV,r,initV,1])

            self.code += tree.children[0].value


        elif tree.children[0] == "(":
            r = self.visit(tree.children[1])

        return r

grammar = '''
start: BEGIN program END
program: instruction+
instruction: declaration | comment | operation
declaration: atomic | structure
operation: atrib | print | read | cond | cicle
print: "print" PE (VARNAME | ESCAPED_STRING) PD PV
read: "read" PE VARNAME PD PV
cond: IF PE op PD body (ELSE body)?
cicle: ciclewhile | ciclefor | ciclerepeat
ciclewhile: WHILE PE op PD body
WHILE: "while"
ciclefor: FOR PE (initcicle (VIR initcicle)*)? PV op PV (inc | dec (VIR (inc | dec))*)? PD body
initcicle: VARNAME EQUAL op
FOR: "for"
ciclerepeat: REPEAT PE (SIGNED_INT | VARNAME) PD body
REPEAT: "repeat"
body: open program close
atrib: VARNAME EQUAL op PV
inc: VARNAME INC
INC: "++"
dec: VARNAME DEC
DEC: "--"
op: NOT op | op (AND | OR) factcond | factcond
NOT: "!"
AND: "&"
OR: "#"
factcond: factcond BINSREL expcond | expcond
BINSREL: LESSEQ | LESS | MOREEQ | MORE | EQ | DIFF
LESSEQ: "<="
LESS: "<"
MOREEQ: ">="
MORE: ">"
EQ: "=="
DIFF: "!="
expcond: expcond (PLUS | MINUS) termocond | termocond
PLUS: "+"
MINUS: "-"
termocond: termocond (MUL|DIV|MOD) factor | factor
MUL: "*"
DIV: "/"
MOD: "%"
factor: PE op PD | SIGNED_INT | VARNAME | DECIMAL
atomic: TYPEATOMIC VARNAME (EQUAL elem)? PV
structure: (set | list | dict | tuple) PV
set: "set" VARNAME (EQUAL OPENBRACKET (elem (VIR elem)*)? CLOSEBRACKET)?
dict: "dict" VARNAME (EQUAL OPENBRACKET (elem DD elem (VIR elem DD elem)*)? CLOSEBRACKET)?
list: "list" VARNAME (EQUAL OPENSQR (elem (VIR elem)*)? CLOSESQR)?
tuple: "tuple" VARNAME (EQUAL PE (elem (VIR elem)*)? PD)?
elem: ESCAPED_STRING | SIGNED_INT | DECIMAL | op
TYPEATOMIC: "int" | "float" | "string" 
VARNAME: WORD
comment: C_COMMENT
BEGIN: "-{"
END: "}-"
PV: ";"
VIR: ","
OPENBRACKET: "{"
CLOSEBRACKET: "}"
OPENSQR: "["
CLOSESQR: "]"
DD: ":"
PE: "("
PD: ")"
EQUAL: "="
open: OPEN
OPEN: "{"
close: CLOSE
CLOSE: "}"
IF: "if"
ELSE: "else"


%import common.WORD
%import common.SIGNED_INT
%import common.DECIMAL
%import common.WS
%import common.ESCAPED_STRING
%import common.C_COMMENT
%ignore WS
'''

parserLark = Lark(grammar)
example = '''-{ 
/*atoms*/
int a;
read(a);
int b = 1 + 1;
float c;
float d = 3.4;
string e;
string f = "ola";

z = 3;

/*structures*/
set g;
set h = {};
set i = {1,"ola", 3.2};

list j;
list k = [];
list l = [1,"ola", 3.2];

tuple m;
tuple n = ();
tuple o = (1,"ola", 3.2);

dict p;
dict q = {};
dict r = {1:"ola", 3.2:"mundo"};

while(a < 0){
    print("while");
}

for(a = 0; a < 20; a++){
print("oi");
}
repeat(5){
    print("ola");
}

if(a == 0){
    if(c == 3){
        print("olaMundo");
        for(a = 3; a == 3; a++){
            print("reset");
            if(c != 3){
                print(b);
            }
        }
    }
}
if(a == 1){
    if(a == 0){
        print("coco");
    }
}
}-
'''
parse_tree = parserLark.parse(example)
data = MyInterpreter().visit(parse_tree)

def geraHTML(atomic_vars, struct_vars, warnings, errors, nrStructs, instrucoes, output_html, control):
    output_html.write("<!DOCTYPE html>")
    output_html.write("<html lang=\"pt\">")
    output_html.write("<head>")
    output_html.write("<meta charset=\"UTF-8\">")
    output_html.write("<link rel=\"stylesheet\" href=\"https://www.w3schools.com/w3css/4/w3.css\">")
    output_html.write("<title>EG - TP2</title>")
    output_html.write("</head>")

    output_html.write("<body>")
    output_html.write("<h1> Tabela com todas as variáveis atómicas do programa </h1>")
    output_html.write("<table class=\"w3-table w3-table-all w3-hoverable\">")
    output_html.write("<tr class=\"w3-yellow\">")
    output_html.write("<th>Variável</th>")
    output_html.write("<th>Tipo</th>")
    output_html.write("<th>Valor</th>")
    output_html.write("<th>Warnings</th>")
    output_html.write("<th>Erros</th>")
    output_html.write("</tr>")

    for var in atomic_vars.keys():
        output_html.write("<tr>")
        output_html.write("<td>" + var + "</td>")
        output_html.write("<td>" + str(atomic_vars[var][0]) + "</td>")
        output_html.write("<td>" + str(atomic_vars[var][1]) + "</td>")
        if var in warnings.keys():
            output_html.write("<td>" + str(warnings[var]) + "</td>")
        
        if var in errors.keys():
            output_html.write("<td>" + str(errors[var]) + "</td>")
          
        output_html.write("</tr>")
    output_html.write("</table>")

    output_html.write("<h1> Tabela com todas as estruturas do programa </h1>")
    output_html.write("<table class=\"w3-table w3-table-all w3-hoverable\">")
    output_html.write("<tr class=\"w3-yellow\">")
    output_html.write("<th>Variável</th>")
    output_html.write("<th>Tipo</th>")
    output_html.write("<th>Tamanho</th>")
    output_html.write("<th>Valor</th>")
    output_html.write("<th>Warnings</th>")
    output_html.write("</tr>")

    for var in struct_vars.keys():
        output_html.write("<tr>")
        output_html.write("<td>" + var + "</td>")
        output_html.write("<td>" + str(struct_vars[var][0]) + "</td>")
        output_html.write("<td>" + str(struct_vars[var][1]) + "</td>")
        output_html.write("<td>" + str(struct_vars[var][2]) + "</td>")

        if var in warnings.keys():
            output_html.write("<td>" + str(warnings[var]) + "</td>")

        output_html.write("</tr>")

    output_html.write("</table>")

    output_html.write("<h1> Total de variáveis do programa: " + str(len(atomic_vars.keys()) + len(struct_vars.keys())) + "</h1>")

    output_html.write("<h1> Tipos de dados estruturados usados </h1>")
    output_html.write("<table class=\"w3-table w3-table-all w3-hoverable\">")
    output_html.write("<tr class=\"w3-yellow\">")
    output_html.write("<th>Tipo</th>")
    output_html.write("<th>Número</th>")
    output_html.write("</tr>")

    for type in nrStructs.keys():
        output_html.write("<tr>")
        output_html.write("<td>" + type + "</td>")
        output_html.write("<td>" + str(nrStructs[type]) + "</td>")
        output_html.write("</tr>")

    output_html.write("</table>")

    output_html.write("<h1> Número total de instruções </h1>")
    output_html.write("<table class=\"w3-table w3-table-all w3-hoverable\">")
    output_html.write("<tr class=\"w3-yellow\">")
    output_html.write("<th>Instrução</th>")
    output_html.write("<th>Número</th>")
    output_html.write("</tr>")

    total = 0

    for instrucao in instrucoes.keys():
        output_html.write("<tr>")
        output_html.write("<td>" + instrucao + "</td>")
        output_html.write("<td>" + str(instrucoes[instrucao]) + "</td>")
        output_html.write("</tr>")
        total += instrucoes[instrucao]

    output_html.write("<td>Total</td>")
    output_html.write("<td>" + str(total) + "</td>")
    output_html.write("</table>")

    ##

    output_html.write("<h1> Estruturas de controlo </h1>")
    output_html.write("<table class=\"w3-table w3-table-all w3-hoverable\">")
    output_html.write("<tr class=\"w3-yellow\">")
    output_html.write("<th>ID</th>")
    output_html.write("<th>Type</th>")
    output_html.write("<th>Parents</th>")
    output_html.write("</tr>")

    total = 0

    for c in control.keys():
        output_html.write("<tr>")
        output_html.write("<td>" + str(c) + "</td>")
        output_html.write("<td>" + str(control[c][0]) + "</td>")
        output_html.write("<td>" + str(control[c][2]) + "</td>")
        output_html.write("</tr>")
        total += 1

    output_html.write("<td>Total</td>")
    output_html.write("<td>" + str(total) + "</td>")
    output_html.write("</table>")

    output_html.write("</body>")
    output_html.write("</html>")

output_html = open("output.html", "w")

#1 e 2 e 3
geraHTML(data["atomic_vars"],data["struct_vars"], data["warnings"], data["errors"], data["nrStructs"],
data["instructions"] ,output_html, data["controlStructs"])

print(data["if_depth"])

## juntar if 0 a n

# cond = cond_0 and cond_1 and ... and cond_n
# visit(cond)
# visit(body_n)

with open("outTest.ntz","w") as file:
    file.write(data["code"])

html_header = '''<!DOCTYPE html>
<html>
    <style>
        .error {
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted black;
            color: red;
        }

        .code {
            position: relative;
            display: inline-block;
        }

        .comment {
            position: relative;
            display: inline-block;
            color: grey;
        }

        .error .errortext {
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px 0;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -40px;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .error .errortext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 20%;
            margin-left: -5px;
            border-width: 5px;
            1border-style: solid;
            border-color: #555 transparent transparent transparent;
        }

        .error:hover .errortext {
            visibility: visible;
            opacity: 1;
        }
    </style>'''

html = html_header + "<body>\n" + data["html_body"] + "\n</body></html>"


with open("codeHTML.html","w") as out:
    out.write(html)

print(data["html_body"])