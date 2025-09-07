"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        # Your code goes here!
        self.class_scope = {}
        self.subroutine_scope = {}
        self.indexes = {
            'STATIC': 0,
            'FIELD': 0,
            'ARG': 0,
            'VAR': 0
        }
        
    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        # Your code goes here!
        self.subroutine_scope = {}
        self.indexes['ARG'] = 0
        self.indexes['VAR'] = 0

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        # Your code goes here!
        if kind in ["STATIC", "FIELD"]:
            self.class_scope[name] = {'type': type, 'kind': kind, 'index': self.indexes[kind]}
            self.indexes[kind] += 1
        elif kind in ["ARG", "VAR"]:
            self.subroutine_scope[name] = {'type': type, 'kind': kind, 'index': self.indexes[kind]}
            self.indexes[kind] += 1

    def is_var(self, name: str) -> bool:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            bool: whether the named identifier is known in the current scope.
        """
        return name in self.subroutine_scope or name in self.class_scope
        
    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        return self.indexes[kind]

    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        # Your code goes here!
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]['kind']
        elif name in self.class_scope:
            return self.class_scope[name]['kind']
        else:
            return 'subroutine'

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        # Your code goes here!
        return self.subroutine_scope[name]['type'] if name in self.subroutine_scope else self.class_scope[name]['type']

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        # Your code goes here!
        return self.subroutine_scope[name]['index'] if name in self.subroutine_scope else self.class_scope[name]['index']
