#  Files

The rdiff tool uses two different files for remote synchronization of files:

 1. Signature File
 2. Delta File

## Signature File

The signature file stores the weak checksum and the strong checksum of "N" equally sized blocks/chunks of the file. This file is sent over the network to the machine which wants to synchronize its local copy.

## Delta File

This file is created on the client machine, using the signature file and the local copy. This file contains instructions on how to construct the new file(file present on the remote machine). The delta file contains either literal bytes or references to block indices in the old file/local copy.
The literal bytes are the missing part. These bytes are present in the remote file and missing on the local copy. 

## Patch Operation
A patching operation is performed using the old file/local copy, and the delta file. The result is a new file which is the same as the one present on the remote machine.