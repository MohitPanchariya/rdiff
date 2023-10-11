#  File Formats
There are a few options to select from:

 1. A json format
 2. Serialized Objects
 3. A custom binary format

Size of the file produced by these techniques is important as we want to send this file over the network.

A json format, though easy to produce,  will be larger in size as compared to a binary format. 
Another option is to serialize the objects representing these files and send it over the network. Serialization has the overhead of metadata which is required for deserialization.
A custom binary format, is probably the most space efficient solution. A comparision between the size of file produced by serialization and the binary format file should be performed to check how much of a difference there is in the size.

The rdiff  utility by librsync uses a custom binary format.

Here are the initial ideas(almost identical to the formats used by rdiff) for custom binary formats.

## Signature File

Header: 

 1. A numerical representation of the weak checksum algorithm(2 bytes).
 2. A numerical representation of the strong checksum algorithm(2 bytes).
 3. Block size(4 bytes).

Therefore, its possible to represent 2^16^ different weak checksum algorithms and strong checksum algorithms, which at the time seems good enough for the foreseeable future.

Body:

The body will consists of blocks of signatures. Each block will consist of the weak 				checksum signature and the strong checksum signature. The size of these signatures will depend on which weak checksum and strong checksum algorithms have been used. These can be inferred from the header.

    Signature File
    struct sigFile{
	    header,
	    body
	}
	
    Signature Header
    struct sigHeader{
	    weakChecksumType,
	    strongChecksumType,
	    blockSize
    }
    
    Signature Body
    struct sigBody{
	    weakChecksum,
	    strongChecksum
    }


## Delta File

    Delta File
    struct deltaFile {
	    header,
	    body
    }
    
    Delta Body
    struct deltaBody {
	    commands[]
    }
    
    Literal Command
    struct literalCommand {
	    commandType,
	    length, // How many bytes to append
	    bytes[] // New data to append
    }
    
    Copy Command
    struct copyCommand {
	    commandType,
	    start, // offset in the old /basis file to begin copying data
	    length // number of bytes to copy from the old/basis file
    }
    
    End Command
    struct endCommand {
	    commandType
    }
	    
Header:
1. 1 byte to represent the delta type.

Body:
1. Series of commands followed by one or more arguments. The size of command is 1 byte.

The commands are:

 1. Literal command: The literal command is followed by two arguments, length indicating the number of bytes to append, followed by the bytes to append.
 2. Copy command: The copy command is followed by two arguments, start indicating the offset in the basis file to begin copying data from, followed by length which indicates how many bytes to copy.
 3. End command: End command doesn't have any arguments. It represents the end of the delta file.
