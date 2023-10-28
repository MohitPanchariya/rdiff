"""
This module contains the Checksum and Signature classes.

Instnaces of the Checksum class can be used to compute the weak, 
the rolling and the strong checksums. 
Refer the link below for more info about the checksums:
https://rsync.samba.org/tech_report/node2.html

Instances of the Signature class can be used to create the signature file using
a basis file.
"""

import hashlib
from functools import partial


class Checksum:
    """
    This class can be used to compute the weak and strong checksums.
    The strong checksum used in this class is the MD4 hash.
    The rolling checksum used is the same as the one described in the rsync
    algorithm paper.
    More information about the weak checksum can be found at the link below:
    https://rsync.samba.org/tech_report/node2.html
    """

    def __init__(self) -> None:
        self.modulus = 2**16

    def weakChecksum(self, block: bytes, startIndex: int, endIndex: int):
        """
        Calculate the weak checksum for the block.
        The weak checksum is the same as the one
        used in the rsync algorithm.
        https://rsync.samba.org/tech_report/node3.html
        """
        a = b = s = 0
        blockSize = len(block)

        if blockSize != (endIndex - startIndex + 1):
            raise Exception(
                "Inconsistent start and end index. Doesn't match block size."
            )

        i = startIndex
        for byte in block:
            a += byte
            b += (endIndex - i + 1) * byte

            i += 1

        a %= self.modulus
        b %= self.modulus

        s = a + (self.modulus * b)

        return (a, b, s)

    def rollingChecksum(
        self,
        previousChecksumA: int,
        previousChecksumB: int,
        previousByte: int,
        endByte: int,
        startIndex: int,
        endIndex: int,
    ):
        """
        The rolling checksum function is used to compute the weak checksum
        on a rolling basis.
        More information about the rolling checksum can be found at the link
        below:
        https://rsync.samba.org/tech_report/node3.html
        """
        checksumA = (previousChecksumA - previousByte + endByte) % self.modulus
        checksumB = (
            previousChecksumB
            - (((endIndex - 1) - (startIndex - 1) + 1) * (previousByte))
            + checksumA
        ) % self.modulus

        checksumS = checksumA + (self.modulus * checksumB)

        return (checksumA, checksumB, checksumS)

    def strongChecksum(self, block: bytes):
        """
        Calculate the strong checksum for the block.
        The hash algorithm used is md4, same as the
        one used in the rsync algorithm.
        https://rsync.samba.org/tech_report/node2.html
        """
        return hashlib.new("md4", block).digest()

    def weakChecksumSize():
        """
        Size of weak checksum in bytes
        """
        return 4

    def strongChecksumSize():
        """
        Size of strong checksum in bytes
        """
        return 16


class Signature:
    """
    Instances of the Signature class primarily used to create the signature
    file using the create signature method.
    These signatures are sent over to the machine which has the updated file.
    """

    # Sizes in bytes
    WEAK_CHECKSUM_SIZE = 2
    STRONG_CHECKSUM_SIZE = 2
    BLOCK_SIZE = 4

    def __init__(self, checksum: Checksum, blockSize: int = 1024):
        self.blockSize = blockSize
        self.checksum = checksum

    def setBlockSize(self, blockSize: int):
        """
        The basis file is divided into equal sized blocks. Set the size of the
        block.
        """
        self.blockSize = blockSize

    def createSignature(self, basisFilePath, sigFilePath):
        """
        Create the signature file. The signatures are
        written to the sigFilePath.
        In this POC its assumed that there is only one
        weak checksum type and only strong checksum type.
        Hence, the header remains the same for any signature
        file.
        The size of the weak checksum is 4 bytes and the size
        of the strong checksum is 16 bytes.
        """
        with open(basisFilePath, "rb") as basisFile, open(sigFilePath, "wb") as sigFile:
            # Write header to the signature file
            weakChecksumType = 0
            strongChecksumType = 0

            sigFile.write(
                weakChecksumType.to_bytes(self.WEAK_CHECKSUM_SIZE, byteorder="big")
            )
            sigFile.write(
                strongChecksumType.to_bytes(self.STRONG_CHECKSUM_SIZE, byteorder="big")
            )
            sigFile.write(self.blockSize.to_bytes(self.BLOCK_SIZE, byteorder="big"))

            weakChecksumSize = Checksum.weakChecksumSize()

            startIndex = 0
            endIndex = 0

            for block in iter(partial(basisFile.read, self.blockSize), b""):
                blockSize = len(block)
                endIndex += blockSize - 1
                _, _, weakChecksum = self.checksum.weakChecksum(
                    block, startIndex, endIndex
                )
                strongChecksum = self.checksum.strongChecksum(block)

                sigFile.write(weakChecksum.to_bytes(weakChecksumSize, byteorder="big"))

                sigFile.write(strongChecksum)

                startIndex = endIndex
