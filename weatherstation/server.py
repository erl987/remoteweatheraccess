"""Implements the communcation with the weather data server.

Functions:
transferto:                 Transfers the given data files to the server.
"""
import os
from datetime import datetime as dt
from ftplib import FTP
from zipfile import ZipFile


def transferto(ftp_server, user_name, passwd, ftp_folder, data_folder, data_file_list, port=21):
    """Transfers the given data files to the server.

    Args:
    ftp_server:             Address of the FTP-server (operated in the passive mode).
    user_name:              User name for the account on the FTP-server.
    passwd:                 Password for the account on the FTP-server.
    ftp_folder:             Folder on the FTP-server to which data should be transferred
    data_folder:            Folder in which the files to be transfered are located.
    data_file_list:         String list with all files in 'data_folder' to be transfered to the server.
    port:                   Connection port of the FTP-server (default: port 21)

    Returns:
    zip_file_name:          Name of the temporary ZIP-file transfered to the server

    Raises:
    The function will raise errors in case of network failures. See ftp-lib documentation for details depending on the type of error.
    """
    with FTP() as ftp:
        # connect to the FTP-server
        ftp.connect( ftp_server, port )

        # Compress all files into a single ZIP-file
        zip_file_name = dt.now().strftime( '%d%m%y_%H%M%S_%f' ) + '_' + user_name + '.zip'
        with ZipFile( data_folder + '/' + zip_file_name, 'w' ) as zip_file:
            for data_file in data_file_list:
                # generate unique file name containing the modification date of the file
                file_timestamp = dt.fromtimestamp( os.path.getmtime( data_folder + '/' + data_file ) )
                server_file_name = file_timestamp.strftime( '%d%m%y_%H%M%S_%f' ) + "_" + data_file
                zip_file.write( data_folder + '/' + data_file, server_file_name )

        # Send single ZIP-file to the server
        ftp.login( user = user_name, passwd = passwd )
        ftp.set_pasv( True )
        ftp.cwd( ftp_folder )
        with open( data_folder + '/' + zip_file_name, 'rb' ) as f:
            ftp.storbinary( "STOR " + zip_file_name, f )

        # Delete the ZIP-file
        os.remove( data_folder + '/' + zip_file_name )

        return zip_file_name

        
