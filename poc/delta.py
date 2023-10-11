from functools import partial

class Delta:

    #Sizes in bytes
    WEAK_CHECKSUM_TYPE_SIZE = 2
    STRONG_CHECKSUM_TYPE_SIZE = 2
    BLOCK_SIZE = 4

    #size in bytes
    WEAK_CHECKSUM_SIZE = 4
    STRONG_CHECKSUM_SIZE = 16

    def __init__(self):
        self.signatures = {}

    def createSignatureDict(self, sigFilePath):

        with open(sigFilePath, "rb") as sigFile:
            #Read the header
            weakChecksumType = sigFile.read(self.WEAK_CHECKSUM_TYPE_SIZE)
            strongChecksumType = sigFile.read(self.STRONG_CHECKSUM_TYPE_SIZE)
            blockSize = sigFile.read(self.BLOCK_SIZE)

            blockIndex = 0

            for weakChecksum in iter(partial(sigFile.read, self.WEAK_CHECKSUM_SIZE), b''):
                
                weakChecksum = int.from_bytes(weakChecksum, byteorder="big")

                strongChecksum = sigFile.read(self.STRONG_CHECKSUM_SIZE)

                self.signatures[weakChecksum] = [blockIndex, strongChecksum]

                blockIndex += 1