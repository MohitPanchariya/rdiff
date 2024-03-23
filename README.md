#  RDIFF

This project is an implementation of the rdiff tool of librsync used for finding
the diff of a file on a remote machine.
(https://github.com/librsync/librsync/blob/master/doc/rdiff.md). 

## Note:
This tool isn't concerned with how the signature, and delta files are
sent/received over the network. It's only concerned with working with these files
and performing the patch.