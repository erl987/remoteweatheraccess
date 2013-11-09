"""Implements the communcation with the weather data server.

Functions:
transferto:                 Transfers the given data files to the server.
"""
import os
from datetime import datetime as dt
from ftplib import FTP


def transferto(ftp_server, user_name, passwd, ftp_folder, data_folder, data_file_list):
    """Transfers the give data files to the server.

    Args:
    ftp_server:             Address of the FTP-server.
    user_name:              User name for the account on the FTP-server.
    passwd:                 Password for the account on the FTP-server.
    ftp_folder:             Folder on the FTP-server to which data should be transferred
    data_folder:            Folder in which the files to be transfered are located.
    data_file_list:         String list with all files in 'data_folder' to be transfered to the server.

    Returns:
    None

    Raises:
    The function will raise errors in case of network failures. See ftp-lib documentation for details depending on the type of error.
    """
    with FTP( ftp_server ) as ftp:
        ftp.login( user = user_name, passwd = passwd )
        
        for data_file in data_file_list:
            # generate unique file name containing the modification date of the file
            file_timestamp = dt.fromtimestamp( os.path.getmtime( data_folder + data_file ) )
            server_file_name = file_timestamp.strftime( '%d%m%y_%H%M' ) + "_" + data_file

            # change to the subfolder
            ftp.cwd( ftp_folder )

            # send file to the server
            with open( data_folder +  data_file, 'rb' ) as f:
                ftp.storbinary( "STOR " + server_file_name, f )
