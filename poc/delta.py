from functools import partial
from signature import Checksum, Signature


class Delta:
    # Sizes in bytes
    WEAK_CHECKSUM_TYPE_SIZE = 2
    STRONG_CHECKSUM_TYPE_SIZE = 2
    BLOCK_SIZE = 4

    # size in bytes
    WEAK_CHECKSUM_SIZE = 4
    STRONG_CHECKSUM_SIZE = 16

    # Delta File Command Representations
    END_COMMAND = 0
    LITERAL_COMMAND = 1
    COPY_COMMAND = 2

    def __init__(self):
        self.signatures = {}

    def __createSignatureDict(self, sigFilePath):
        with open(sigFilePath, "rb") as sigFile:
            # Read the header
            weakChecksumType = sigFile.read(self.WEAK_CHECKSUM_TYPE_SIZE)
            strongChecksumType = sigFile.read(self.STRONG_CHECKSUM_TYPE_SIZE)
            blockSize = sigFile.read(self.BLOCK_SIZE)

            blockIndex = 0

            for weakChecksum in iter(
                partial(sigFile.read, self.WEAK_CHECKSUM_SIZE), b""
            ):
                weakChecksum = int.from_bytes(weakChecksum, byteorder="big")

                strongChecksum = sigFile.read(self.STRONG_CHECKSUM_SIZE)

                self.signatures[weakChecksum] = [blockIndex, strongChecksum]

                blockIndex += 1

    def __writeCopyCommand(self, deltaFile, blockIndex, blockSize):
        # The size of the command is 1 byte
        deltaFile.write(self.COPY_COMMAND.to_bytes(1, byteorder="big"))
        # Write the block index/offset.
        deltaFile.write(blockIndex.to_bytes(4, byteorder="big"))
        # Write the size of the block to copy.
        deltaFile.write(blockSize.to_bytes(4, byteorder="big"))

    def __writeLiteralCommand(self, deltaFile, buffer):
        deltaFile.write(self.LITERAL_COMMAND.to_bytes(1, byteorder="big"))
        deltaFile.write(len(buffer).to_bytes(4, byteorder="big"))
        deltaFile.write(buffer)

        buffer.clear()

    def createDeltaFile(
        self, inFilePath, deltaFilePath, sigFielPath, blockSize: int, checksum: Checksum
    ):
        self.__createSignatureDict(sigFielPath)
        signatures = self.signatures

        """
        Store the previous command written to the delta file.
        Useful to batch literal commands.
        """
        previousCommand = -1

        with open(inFilePath, "rb") as inFile, open(deltaFilePath, "wb") as deltaFile:
            startIndex = 0
            firstBlock = True

            for block in iter(partial(inFile.read, blockSize), b""):
                endIndex = (startIndex) + (len(block) - 1)

                if firstBlock:
                    a, b, weakChecksum = checksum.weakChecksum(
                        block, startIndex, endIndex
                    )
                    matched = False
                else:
                    """
                    If the previous block's strong checksum matched, find the
                    regular weak checksum
                    """
                    if matched:
                        a, b, weakChecksum = checksum.weakChecksum(
                            block, startIndex, endIndex
                        )
                    # Else find the rolling checksum at an offset of one byte
                    else:
                        a, b, weakChecksum = checksum.rollingChecksum(
                            a,
                            b,
                            previousByte,
                            block[len(block) - 1],
                            startIndex,
                            endIndex,
                        )

                if weakChecksum in signatures:
                    strongChecksum = checksum.strongChecksum(block)
                    if signatures[weakChecksum][1] == strongChecksum:
                        matched = True
                        startIndex = endIndex + 1

                        # if not firstBlock:
                        if previousCommand == self.LITERAL_COMMAND:
                            self.__writeLiteralCommand(deltaFile, literalBuffer)

                        # Get the block index of the matched block
                        blockIndex = signatures[weakChecksum][0]
                        blockSize = len(block)
                        """
                        The reason to call it previous command is that when a
                        literal command is issued, the literals can be batched
                        based on whether the previous command was a literal command
                        or not. Hence, as a way to determine if the byte can be 
                        batched, the previousCommand variable is maintained.
                        """
                        previousCommand = self.COPY_COMMAND

                        self.__writeCopyCommand(deltaFile, blockIndex, blockSize)

                else:
                    matched = False

                if not matched:
                    startIndex += 1

                    previousByte = block[0]
                    inFile.seek(startIndex, 0)

                    previousCommand = self.LITERAL_COMMAND
                    """
                    Since there isn't a match, write a literal command.
                    Maintain a buffer of literal bytes.
                    These bytes are not written immediately so that they can
                    be batched. This is to reduce the overhead of the literal
                    command. If they aren't batched, the size taken by the over
                    heads exceeds the size of the data, which is only one byte.
                    The literal command takes one byte, the length will take a byte
                    followed by the byte. Thats 2 bytes of overhead per one byte of
                    literal data. This leads to wastage.
                    """
                    if firstBlock:
                        literalBuffer = bytearray()
                        firstBlock = False
                    literalBuffer.append(block[0])

            # If there is anything left in the buffer, write it to the file
            if previousCommand == self.LITERAL_COMMAND:
                self.__writeLiteralCommand(deltaFile, literalBuffer)

            # Write the end commnad to the delta file.
            deltaFile.write(self.END_COMMAND.to_bytes(1, byteorder="big"))
