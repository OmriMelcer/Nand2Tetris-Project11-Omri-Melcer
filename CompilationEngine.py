"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter
class CompilationEngine:
    """
    Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, input_stream: JackTokenizer, output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.current_type_processed = ""
        self.vm_writer = VMWriter(output_stream)
        self.symbol_table = SymbolTable()
        self.if_else_counter = 0
        self.while_counter = 0
        self.class_name = ""
        self.compile_class()

    def compile_class(self) -> None:
        """Compiles a complete class."""
        # Your code goes here!
        self.input_stream.advance() # class
        self.input_stream.advance() # class name
        self.class_name = self.input_stream.identifier()
        self.input_stream.advance() # {
        self.input_stream.advance() # class var dec
        self.compile_class_var_dec()
        self.compile_subroutine()
        #self.input_stream.advance() #TODO check if needed
        self.input_stream.advance() # }

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        self.compile_all_vars_in_dec(True)

    # VX
    def compile_all_vars_in_dec(self, is_class_var_dec: bool) -> int:
        self.input_stream.advance()
        type_of_var = "classVarDec" if is_class_var_dec else "varDec"
        lst_to_be_in = ["static", "field"] if is_class_var_dec else ['var']
        while self.input_stream.token_type() == "KEYWORD" and self.input_stream.keyword() in lst_to_be_in:
            kind_of_var = self.input_stream.keyword()
            self.input_stream.advance()
            type_of_var = self.input_stream.identifier()
            self.input_stream.advance()
            var_name = self.input_stream.identifier()
            self.symbol_table.define(var_name, type_of_var, kind_of_var.upper())
            self.input_stream.advance()
            while self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() == ",":
                self.input_stream.advance()
                var_name = self.input_stream.identifier()
                self.symbol_table.define(var_name, type_of_var, kind_of_var.upper())
                self.input_stream.advance() # , or ;
            self.input_stream.advance() # moving to next token after ;
        return self.symbol_table.var_count("VAR") if not is_class_var_dec else -1

    # VX
    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        while self.input_stream.token_type() == "KEYWORD" and self.input_stream.keyword() in ["constructor", "function", "method"]:
            function_type = self.input_stream.keyword()
            self.symbol_table.start_subroutine()
            if function_type == "method":
                self.symbol_table.define("this", self.class_name, "ARG")
            self.input_stream.advance() # function kind -> function type (current)
            function_type_is_void = self.input_stream.identifier() == "void" # only care about void because other types are not important for the vm code, and void functions push constant 0 at the end
            self.input_stream.advance() # function type -> function name (current)
            function_name = self.input_stream.identifier()
            function_name_full = f"{self.class_name}.{function_name}"
            self.input_stream.advance() # function name -> (
            self.input_stream.advance() # ( -> type of first parameter or ) 
            arg_count = self.compile_parameter_list()
            self.input_stream.advance() # { -> var dec or statements
            local_count = self.compile_var_dec()
            self.vm_writer.write_function(function_name_full, local_count)
            if function_type == "method":
                self.vm_writer.write_push("argument", 0)
                self.vm_writer.write_pop("pointer", 0)
            # self.output_stream.advance()
            if function_type == "constructor":
                self.vm_writer.write_push("constant", self.symbol_table.var_count("FIELD"))
                self.vm_writer.write_call("Memory.alloc", 1)
                self.vm_writer.write_pop("pointer", 0)
            self.compile_statements()
            if function_type_is_void:
                self.vm_writer.write_push("constant", 0)
            self.input_stream.advance() #

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        while not self.input_stream.token_type == "SYMBOL" and self.input_stream.symbol() != ')':
            type_of_var = self.input_stream.identifier()
            self.input_stream.advance() # type -> var name
            var_name = self.input_stream.identifier()
            self.symbol_table.define(var_name, type_of_var, "ARG")
            self.input_stream.advance() #var name -> , or )
            if self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() == ",":
                self.input_stream.advance()
        self.input_stream.advance() # ) -> {
        return self.symbol_table.var_count("ARG")

    def compile_var_dec(self) -> int:
        """Compiles a var declaration."""
        return self.compile_all_vars_in_dec(False)

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        self.output_stream.write("<statements>\n")
        while self.input_stream.token_type() == "KEYWORD" and self.input_stream.keyword() in ["let", "if", "while", "do", "return"]:
            if self.input_stream.keyword() == "let":
                self.compile_let()
            elif self.input_stream.keyword() == "if":
                self.compile_if()
            elif self.input_stream.keyword() == "while":
                self.compile_while()
            elif self.input_stream.keyword() == "do":
                self.compile_do()
            elif self.input_stream.keyword() == "return":
                self.compile_return()
            # TODO: check if advanced is need here.
            # self.input_stream.advance()
        self.output_stream.write("</statements>\n")

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Your code goes here!
        self.input_stream.advance() #do to subroutine call
        self.compile_subroutine_call()
        self.input_stream.advance() # ; after the subroutine call

    def compile_subroutine_call(self, first_token: str = "") -> None:
        """
        Compiles a subroutine call.
        """
        if first_token == "":
            first_token = self.input_stream.identifier()
            self.input_stream.advance()
        # self.output_stream.write(f"<identifier> {first_token} </identifier>\n") #className | subroutineName
        # self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n")
        second_token = ""
        if self.input_stream.symbol() == ".":
            self.input_stream.advance() # . to subroutineName
            second_token = self.input_stream.identifier()
            self.input_stream.advance() # subroutineName to (
        self.input_stream.advance()
        arg_num = 0
        class_of_var = ""
        if second_token != "":
            if self.symbol_table.is_var(first_token):
                self.push_variable(first_token)
                arg_num += 1
                class_of_var = f"{self.symbol_table.type_of(first_token)}."
            else:
                class_of_var = f"{first_token}."
        else:
            second_token = first_token
        arg_num += self.compile_expression_list()
        function_call = class_of_var + second_token
        self.vm_writer.write_call(function_call, arg_num)
        self.input_stream.advance()


    def compile_let(self) -> None:
        """Compiles a let statement."""
        # Your code goes here!
        self.input_stream.advance() #let -> where to push
        first_identifier = self.input_stream.identifier()
        self.input_stream.advance()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # = or [
        if self.input_stream.symbol() == "[":
            self.input_stream.advance()
            self.compile_expression() #TODO: should finish after the advancing to the ] token
            self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # ]
            self.input_stream.advance()
            self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # =
        self.input_stream.advance()
        self.compile_expression()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # ;
        self.input_stream.advance()
        self.output_stream.write("</letStatement>\n")

    def compile_while(self) -> None:
        """Compiles a while statement.
            receive it with current token as 'while'
            returns it with current token as the after }
        """
        self.output_stream.write("<whileStatement>\n")
        self.output_stream.write(f"<keyword> {self.input_stream.keyword()} </keyword>\n") #while
        self.input_stream.advance()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # (
        self.input_stream.advance()
        self.compile_expression()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # )
        self.input_stream.advance()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # {
        self.input_stream.advance()
        self.compile_statements()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # }
        self.input_stream.advance()
        self.output_stream.write("</whileStatement>\n")

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.output_stream.write("<returnStatement>\n")
        self.output_stream.write(f"<keyword> {self.input_stream.keyword()} </keyword>\n") #return
        self.input_stream.advance()
        if not (self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() == ";"):
            self.compile_expression()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # ;
        self.input_stream.advance()
        self.output_stream.write("</returnStatement>\n")

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # Your code goes here!
        self.output_stream.write("<ifStatement>\n")
        self.output_stream.write(f"<keyword> {self.input_stream.keyword()} </keyword>\n") #if
        self.input_stream.advance()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # (
        self.input_stream.advance()
        self.compile_expression()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # )
        self.input_stream.advance()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # {
        self.input_stream.advance()
        self.compile_statements()
        self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # }
        self.input_stream.advance()
        # Optional else clause
        if self.input_stream.keyword() == "else":
            self.output_stream.write(f"<keyword> {self.input_stream.keyword()} </keyword>\n") # else
            self.input_stream.advance()
            self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # {
            self.input_stream.advance()
            self.compile_statements()
            self.output_stream.write(f"<symbol> {self.input_stream.symbol()} </symbol>\n") # }
            self.input_stream.advance()
        self.output_stream.write("</ifStatement>\n")

    # *VX 
    def compile_expression(self) -> None:
        """Compiles an expression.
        Should finish at the ) or ] or , token as current
        starts after advancing to the first token
        """
        self.compile_term()
        while self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() in self.input_stream.ops:
            operand = self.input_stream.symbol()
            self.input_stream.advance()
            self.compile_term()
            self.handle_op(operand)

   # *VX         
    def handle_key_words(self, keyword: str) -> None:
        if keyword == "true":
            self.vm_writer.write_push("constant", 1)
            self.vm_writer.write_arithmetic("neg")
        elif keyword in ["false", "null"]:
            self.vm_writer.write_push("constant", 0)
        elif keyword == "this":
                self.vm_writer.write_push("pointer", 0)
            
    def handle_op(self, operand: str) -> str:
        if operand == "+":
            self.vm_writer.write_arithmetic("add")
        elif operand == "-":
            self.vm_writer.write_arithmetic("sub")
        elif operand == "*":
            self.vm_writer.write_call("Math.multiply", 2)
        elif operand == "/":
            self.vm_writer.write_call("Math.divide", 2)
        elif operand == "&":
            self.vm_writer.write_arithmetic("and")
        elif operand == "|":
            self.vm_writer.write_arithmetic("or")
        elif operand == "<":
            self.vm_writer.write_arithmetic("lt")
        elif operand == ">":
            self.vm_writer.write_arithmetic("gt")
        elif operand == "=":
            self.vm_writer.write_arithmetic("eq")
    
    def handle_unary_op(self, unary_op: str) -> None:
        if unary_op == "-":
            self.vm_writer.write_arithmetic("neg")
        elif unary_op == "~":
            self.vm_writer.write_arithmetic("not")
        elif unary_op == "^":
            self.vm_writer.write_arithmetic("shiftLeft")
        elif unary_op == "#":
            self.vm_writer.write_arithmetic("shiftRight")

    # *VX
    def compile_term(self) -> None:
        """Compiles a term. 
        the function starts with the current token as the first token of the term.
        The function returns with the current token after the term.
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and  a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        first_token = ""
        if self.input_stream.token_type() == "INT_CONST":
            self.vm_writer.write_push("constant", self.input_stream.int_val())
            self.input_stream.advance()
        elif self.input_stream.token_type() == "STRING_CONST":
            self.handle_string_literal()
            self.input_stream.advance()
        elif self.input_stream.token_type() == "KEYWORD" and self.input_stream.keyword() in ["true", "false", "null", "this"]:
            self.handle_key_words(self.input_stream.keyword())
            self.input_stream.advance()
        elif self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() == "(":
            self.input_stream.advance()
            self.compile_expression()
            # should return with the ')' sign that I'll advance over
            self.input_stream.advance()
        elif self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() in self.input_stream.unaryOps:
            op = self.input_stream.symbol()
            self.input_stream.advance()
            self.compile_term()
            self.handle_unary_op(op)
        else: # an identifier / subroutine call
            first_token = self.input_stream.identifier()
            self.input_stream.advance()
            if self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() == "[":
                self.input_stream.advance()
                self.push_array_entry(first_token, push_value=True)
            elif self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() in ["(", "."]:
                self.compile_subroutine_call(first_token = first_token)
            else:
                self.push_variable(first_token)


    def push_array_entry(self, var_name: str, push_value: bool) -> None:
        # recieves the array name as var_name, recieve the tokeneizer after the '[' returns it after the ']'
        # pushes the value into the stack
        self.push_variable(var_name)
        self.compile_expression()
        self.input_stream.advance() #over the ']'
        self.vm_writer.write_arithmetic("add")
        if push_value:
            self.vm_writer.write_pop("pointer", 1)
            self.vm_writer.write_push("that", 0)

    def push_variable(self, var_name: str) -> None:
        self.vm_writer.write_push(self.symbol_table.kind_of(var_name), self.symbol_table.index_of(var_name))

    def handle_string_literal(self) -> None:
        this_string = self.input_stream.string_val()
        self.vm_writer.write_push("constant", len(this_string))
        self.vm_writer.write_call("String.new", 1)
        for char in this_string:
            self.vm_writer.write_push("constant", ord(char))
            self.vm_writer.write_call("String.append", 2)

    # *VX
    def compile_expression_list(self) -> int:
        # this function ends up pushing into the stack all the expressions in the list inside a function call
        num_expressions = 0
        while not (self.input_stream.token_type () == "SYMBOL" and self.input_stream.symbol() == ")"):
            self.compile_expression()
            num_expressions += 1
            if self.input_stream.token_type() == "SYMBOL" and self.input_stream.symbol() == ",":
                self.input_stream.advance()   
        return num_expressions
