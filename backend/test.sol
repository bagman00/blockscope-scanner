pragma solidity ^0.8.0; contract A { function f() public { address(this).call(""); } }
