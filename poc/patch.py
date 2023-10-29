"""
This module contains the Patch class which is uses the delta file to synchronise
a local copy of a file to have the same contents as the machine sending the
delta file
"""
from functools import partial


class Patch:
    # Delta File Command Representations
    END_COMMAND = 0
    LITERAL_COMMAND = 1
    COPY_COMMAND = 2

    # Size in bytes
    COMMAND_SIZE = 1

    def __init__(self):
        pass

    def patchFile(self, deltaFilePath, basisFilePath, outFilePath):
        with (
            open(deltaFilePath, "rb") as deltaFile,
            open(basisFilePath, "rb") as basisFile,
            open(outFilePath, "wb") as outFile,
        ):
            """
            This function is used to create the final synchronised file using
            the delta file and the basis file.
            """
            for command in iter(partial(deltaFile.read, self.COMMAND_SIZE), b""):
                command = int.from_bytes(command, byteorder="big")
                # Return if reached end of file
                if command == self.END_COMMAND:
                    return

                if command == self.COPY_COMMAND:
                    # Size of block index is represented using 4 bytes in the delta file
                    blockIndex = int.from_bytes(deltaFile.read(4), byteorder="big")
                    # Number of bytes to read is represented using 4 bytes in the delta file
                    bytesToRead = int.from_bytes(deltaFile.read(4), byteorder="big")

                    # Seek to the block to be read
                    basisFile.seek(1024 * blockIndex)

                    block = basisFile.read(bytesToRead)

                    # Write bytes to the out file
                    outFile.write(block)

                elif command == self.LITERAL_COMMAND:
                    # The number of literals to be copied from the delta file is
                    # represented using 4 bytes.
                    bytesToRead = int.from_bytes(deltaFile.read(4), byteorder="big")
                    # Read literals from the delta file
                    block = deltaFile.read(bytesToRead)

                    # Write literals to the out file
                    outFile.write(block)

                else:
                    raise Exception("Undefined Command in delta file.")
