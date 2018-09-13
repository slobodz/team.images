"""Parse and upload images"""
import glob
import os
import sys
import piexif
import pyodbc
import requests
from datetime import datetime
import json
import argparse
from shutil import copy2, move

from team.datasync.api.request import token_refresh
from team.images import logging, app_config
from team.images.entity.model import TeamImage
from team.images.service.utils import exif_tuple_2_str, \
    exif_str_2_tuple, list_to_str, rreplace, get_column_descriptions


'''
TO DO:
-Do not move files to processed folder before image upload (in case of failure)
-Add more command line arguments
-Add config file
-More advanced SQL search - including manufacture check
-Keep templates in separate folder
-Web requests in dedicated method
-Merge TeamImages with TeamAssets
-Refactoring
'''

FILENAME_FILTER = None
IMAGE_CURRENT_ERROR_FOLDER = None
IMAGE_UNPROCESSED_ERROR_FOLDER = None
SQL_CURSOR = None

def process_exif(image_path):
    image_file = Image.open(image_path)
    #exif_data = image_file._getexif()
    #print(exif_data)
    #print(ord(u'ą'))
    '''
    exif_dict = piexif.load(image_path)
    for ifd in ("0th", "Exif", "GPS", "1st"):
        for tag in exif_dict[ifd]:
            print(ifd, piexif.TAGS[ifd][tag]["name"], exif_dict[ifd][tag])
    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in image_file._getexif().items()
        if k in PIL.ExifTags.TAGS
        }
    '''
    if image_file.info.get('exif'):
        exif_dict = piexif.load(image_file.info["exif"])
        if exif_dict.get('0th'):
            if exif_dict["0th"].get(piexif.ImageIFD.XResolution):
                x_dpi, flag = exif_dict["0th"][piexif.ImageIFD.XResolution]
                #print('EXIF_XResolution: ' + str(x_dpi))
            if exif_dict["0th"].get(piexif.ImageIFD.YResolution):
                y_dpi, flag = exif_dict["0th"][piexif.ImageIFD.YResolution]
                #print('EXIF_YResolution: ' + str(y_dpi))
            #ImageDescription and XPTitle are the same when saved on Windows explorer
            if exif_dict["0th"].get(piexif.ImageIFD.ImageDescription):
                img_desc = exif_dict["0th"][piexif.ImageIFD.ImageDescription]
                #print('ImageDescription: ' + img_desc.decode('UTF-8'))
            if exif_dict["0th"].get(piexif.ImageIFD.XPTitle):
                XPTitle = exif_dict["0th"][piexif.ImageIFD.XPTitle]
                #print('XPTitle: ' + exif_tuple_2_str(XPTitle))
            if exif_dict["0th"].get(piexif.ImageIFD.XPSubject):
                XPSubject = exif_dict["0th"][piexif.ImageIFD.XPSubject]
                #print('XPSubject: ' + exif_tuple_2_str(XPSubject))
            if exif_dict["0th"].get(piexif.ImageIFD.XPComment):
                XPComment = exif_dict["0th"][piexif.ImageIFD.XPComment]
                #print('XPComment: ' + exif_tuple_2_str(XPComment))
            if exif_dict["0th"].get(piexif.ImageIFD.XPKeywords):
                XPKeywords = exif_dict["0th"][piexif.ImageIFD.XPKeywords]
                #print('XPKeywords: ' + exif_tuple_2_str(XPKeywords))
            if exif_dict["0th"].get(piexif.ImageIFD.XPAuthor):
                XPAuthor = exif_dict["0th"][piexif.ImageIFD.XPAuthor]
                #print('XPAuthor: ' + exif_tuple_2_str(XPAuthor))

    # process im and exif_dict...
    #exif_dict["0th"][piexif.ImageIFD.XResolution] = (width, 1)
    #exif_dict["0th"][piexif.ImageIFD.YResolution] = (height, 1)
    '''
    exif_dict["0th"][piexif.ImageIFD.XResolution] = 
    exif_dict["0th"][piexif.ImageIFD.YResolution] = 
    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = 'test-title-ąćń'.encode('UTF-8')
    exif_dict["0th"][piexif.ImageIFD.XPSubject] = exif_str_2_tuple(u'xpsubject-ąćń-שלום עולם')
    exif_dict["0th"][piexif.ImageIFD.XPComment] = exif_str_2_tuple(u'xpcomment')
    exif_dict["0th"][piexif.ImageIFD.XPKeywords] = exif_str_2_tuple(u'xpkeywords')
    exif_dict["0th"][piexif.ImageIFD.XPAuthor] = exif_str_2_tuple(u'https://services.teampolska.eu/')
    exif_dict["0th"][piexif.ImageIFD.XPTitle] = exif_str_2_tuple(u'xptitle')
    exif_bytes = piexif.dump(exif_dict)
    image_file.save(os.path.join(folder_name, '1-SP2-KALORIK-test.jpg'), "jpeg", exif=exif_bytes)
    '''
    #print(PIL.ExifTags.TAGS)
    #print(image_file._getexif().items())
    #image_file.save()
    image_file.close()

def check_folder_structure(process_id):
    folders_ok = True
    if not os.path.exists(app_config.PARENT_FOLDER):
        logging.error("Image directory does not exists: '{0}'".format(app_config.PARENT_FOLDER))
        folders_ok = False
    else:
        if not os.path.isdir(app_config.PARENT_FOLDER):
            logging.error("Image directory path: '{0}' is not valid.".format(app_config.PARENT_FOLDER))
            folders_ok = False

    if folders_ok:
        try:
            if not os.path.isdir(app_config.IMAGE_ERROR_FOLDER):
                os.makedirs(app_config.IMAGE_ERROR_FOLDER)
            if not os.path.isdir(IMAGE_CURRENT_ERROR_FOLDER):    
                os.makedirs(IMAGE_CURRENT_ERROR_FOLDER)
            if not os.path.isdir(IMAGE_UNPROCESSED_ERROR_FOLDER): 
                os.makedirs(IMAGE_UNPROCESSED_ERROR_FOLDER)
            if not os.path.isdir(app_config.IMAGE_LOG_FOLDER):
                os.makedirs(app_config.IMAGE_LOG_FOLDER)
            if not os.path.isdir(app_config.IMAGE_PROCESSED_FOLDER):
                os.makedirs(app_config.IMAGE_PROCESSED_FOLDER)
            if not os.path.isdir(app_config.IMAGE_THUMBNAIL_FOLDER):
                os.makedirs(app_config.IMAGE_THUMBNAIL_FOLDER)
            if not os.path.isdir(app_config.IMAGE_UNPROCESSED_FOLDER):
                os.makedirs(app_config.IMAGE_UNPROCESSED_FOLDER)
        except Exception as ex:
            logging.error("Exception occured while creating flder structure. Error description: '{0}'".format(repr(ex)))
            folders_ok = False
    
    if folders_ok:
        #move all items from parent to unprocessed/errors folder
        for filename in os.listdir(app_config.PARENT_FOLDER):
            try:
                if os.path.join(app_config.PARENT_FOLDER, filename) not in [app_config.IMAGE_ERROR_FOLDER, app_config.IMAGE_LOG_FOLDER, app_config.IMAGE_PROCESSED_FOLDER, app_config.IMAGE_THUMBNAIL_FOLDER, app_config.IMAGE_UNPROCESSED_FOLDER]:
                    if os.path.isfile(os.path.join(app_config.PARENT_FOLDER, filename)):
                        if os.path.splitext(filename)[-1].lower() in app_config.ALLOWED_EXTENSIONS:
                            if os.path.isfile(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename)):
                                move(os.path.join(app_config.PARENT_FOLDER, filename), os.path.join(IMAGE_CURRENT_ERROR_FOLDER, filename))
                                logging.warning("File: '{0}' already exists in unprocessed folder and has been moved to destination '{1}'. Object will not be processed.".format(os.path.join(app_config.PARENT_FOLDER, filename), os.path.join(IMAGE_CURRENT_ERROR_FOLDER, filename)))
                            else:
                                move(os.path.join(app_config.PARENT_FOLDER, filename), os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename))
                                logging.info("File: '{0}' was moved to location '{1}'".format(os.path.join(app_config.PARENT_FOLDER, filename), os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename)))
                        else:
                            move(os.path.join(app_config.PARENT_FOLDER, filename), os.path.join(IMAGE_CURRENT_ERROR_FOLDER, filename))
                            logging.warning("File: '{0}' has not allowed extension: '{1}' and has been moved to destination '{2}'. Object will not be processed.".format(os.path.join(app_config.PARENT_FOLDER, filename), os.path.splitext(filename)[-1].lower(), os.path.join(IMAGE_CURRENT_ERROR_FOLDER, filename)))
                    elif os.path.isdir(os.path.join(app_config.PARENT_FOLDER, filename)):
                        move(os.path.join(app_config.PARENT_FOLDER, filename), os.path.join(IMAGE_CURRENT_ERROR_FOLDER, filename))
                        logging.warning("Item: '{0}' is a directory, which is not expected in this location and it was moved to destination: '{1}'. Object will not be processed.".format(os.path.join(app_config.PARENT_FOLDER, filename), os.path.join(IMAGE_CURRENT_ERROR_FOLDER, filename)))
            except PermissionError as ex:
                logging.error("Unable to move item: '{0}' to destination location. Item is opened in another process or current user does not have permission to move it. System error description: '{1}'".format(os.path.join(app_config.PARENT_FOLDER, filename), repr(ex)))
                folders_ok = False
            except Exception as ex:
                logging.error("Exception occured while moving object: '{0}'. System error description: '{1}'".format(os.path.join(app_config.PARENT_FOLDER, filename), repr(ex)))
                folders_ok = False
            except:
                logging.error("Unspecified error occured while moving object: '{0}'").format(os.path.join(app_config.PARENT_FOLDER, filename))
                folders_ok = False
    return folders_ok

    def find_product_code_in_db(team_image, strict_level):
        global SQL_CURSOR
        rowcount = 0
        for product_code in team_image.product_codes:
            product_code_for_like = product_code.replace("'", "''").replace("%", "[%]").replace("_", "[_]")
            sql = ""
            #sql = "SELECT [product_id],[product_code],[product_description] FROM [data].[product]"
            #sql = "SELECT [ID],[Guid],[Kod],[Nazwa],[NumerKatalogowy] FROM [TEAM].[dbo].[Towary] WHERE Kod LIKE '" + product_code_for_like + "%'"
            if strict_level == 1:
                sql = "SELECT [product_id],[product_code],[product_description] FROM [data].[product] WHERE [product_code] = '" + product_code.replace("'", "''") + "'"
            elif strict_level == 2:
                sql = "SELECT [product_id],[product_code],[product_description] FROM [data].[product] WHERE [product_code] LIKE '" + product_code_for_like + "%'"
            elif strict_level == 3:
                sql = "SELECT [product_id],[product_code],[product_description] FROM [data].[product] WHERE [product_code] LIKE '%" + product_code_for_like + "%'"
            elif strict_level == 4:
                sql = "SELECT [product_id],[product_code],[product_description] FROM [data].[product] WHERE REPLACE([product_code],'/','-') LIKE '%" + product_code_for_like + "%'"

            SQL_CURSOR.execute(sql)
            row = SQL_CURSOR.fetchone()
            while row:
                rowcount = rowcount + 1
                if rowcount == 1:
                    team_image.product_code_from_db = row[1].lower().encode('utf-8', 'ignore').decode(sys.stdout.encoding)
                try:
                    team_image.products_from_db.append(
                        str(row[0])+'~"' + row[1]+'"~"'
                        + row[2].lower().encode('utf-8', 'ignore').decode(sys.stdout.encoding).replace('"', '""')+'"')
                except UnicodeDecodeError as ex:
                    logging.error("Error occured while converting product description with code: '{0}'. Error description: '{1}'".format(row[1], repr(ex)))
                #title.encode('utf-8', 'ignore').decode(sys.stdout.encoding)
                #title = title.encode('utf8').decode('utf8')
                #break
                row = SQL_CURSOR.fetchone()
            if rowcount > 1:
                team_image.errors.append('SQL: More than one [' + str(rowcount) + '] product returned for the code: [' + product_code + ']')
            '''
            if rowcount >= 4:
                self.product_code_from_db = ''
                self.products_from_db.clear()
                self.errors.append('SQL: Too many records [' + str(rowcount) + '] returned for the code: [' + product_code + ']')
            '''
        return rowcount

#========================================================= SCRIPT =========================================================#
def full_refresh():
    global FILENAME_FILTER
    global IMAGE_CURRENT_ERROR_FOLDER
    global IMAGE_UNPROCESSED_ERROR_FOLDER

    process_id = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f") #get process timestamp/id
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-ll", "--loglevel", choices=['debug','info','warning','error','critical'], default='warning', required=False, help="Information type captured in log file")
    arg_parser.add_argument("-ff", "--filenamefilter", default='', required=False, help="Only files containing this value will be processed (case sensitive)")
    args = vars(arg_parser.parse_args())

    loglevel = logging.WARNING
    if args["loglevel"] == "debug":
        loglevel = logging.DEBUG
    elif args["loglevel"] == "info":
        loglevel = logging.INFO
    elif args["loglevel"] == "warning":
        loglevel = logging.WARNING
    elif args["loglevel"] == "error":
        loglevel = logging.ERROR
    elif args["loglevel"] == "critical":
        loglevel = logging.CRITICAL

    FILENAME_FILTER = args["filenamefilter"]

    logging.basicConfig(handlers=[logging.FileHandler(filename=os.path.join(app_config.IMAGE_LOG_FOLDER, process_id + '.log'), encoding='utf-8')], \
                        format='%(asctime)s:%(levelname)s:%(message)s', level=loglevel) #, level=logging.INFO - default is WARNING
    logging.info("TeamImage process [{0}] version: '{1}'".format(process_id, app_config.VERSION))
    IMAGE_CURRENT_ERROR_FOLDER = os.path.join(app_config.IMAGE_ERROR_FOLDER, process_id)
    IMAGE_UNPROCESSED_ERROR_FOLDER = os.path.join(IMAGE_CURRENT_ERROR_FOLDER, app_config.IMAGE_UNPROCESSED_FOLDER.rsplit('\\', 1)[1])

    if check_folder_structure(process_id) == False:
        logging.critical("Error occured while validating folder structure inside directory: '{0}'".format(app_config.PARENT_FOLDER))
        exit(1)

    sql_driver = ""
    if sys.platform == "linux" or sys.platform == "linux2":
        sql_driver = "{SQL Server}"
    elif sys.platform == "win32" or sys.platform == "win64":
        sql_driver = "{SQL Server Native Client 11.0}"
    else:
        logging.critical("Unsupported system type: '{0}'".format(sys.platform))
        exit(1)

    ConnectionString = app_config.SQL_CONNECTION_STRING_TEMPLATE.replace('%SQL_SERVER%', app_config.TEAM_SERVER)
    ConnectionString = ConnectionString.replace('%SQL_DRIVER%', sql_driver)
    ConnectionString = ConnectionString.replace('%SQL_DATABASE%', app_config.TEAM_DATABASE)
    ConnectionString = ConnectionString.replace('%SQL_LOGIN%', app_config.TEAM_USER)
    ConnectionString = ConnectionString.replace('%SQL_PASSWORD%', app_config.TEAM_PWD)
    try:
        SQL_CONNECTION = pyodbc.connect(ConnectionString)
        logging.info("Connected to server: '{0}'".format(app_config.TEAM_SERVER))
    except Exception as ex:
        logging.critical("Unable to connect to database server: '{0}'. Error: {1}".format(app_config.TEAM_SERVER, repr(ex)))
        exit(1)

    if SQL_CONNECTION is not None:
        SQL_CURSOR = SQL_CONNECTION.cursor()
    #print(get_column_descriptions())
    #onlyfiles = [f for f in listdir(IMAGE_FOLDER) if isfile(join(IMAGE_FOLDER, f))]
    if len(FILENAME_FILTER) > 0:
        logging.warning("File name filter is applied for this run: '{0}'".format(FILENAME_FILTER))

    onlyfiles = os.listdir(app_config.IMAGE_UNPROCESSED_FOLDER)
    for filename in onlyfiles:
        if os.path.isfile(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename)):
            if os.path.splitext(filename)[-1].lower() in app_config.ALLOWED_EXTENSIONS:
                if filename.find(FILENAME_FILTER) >= 0 or len(FILENAME_FILTER.strip()) == 0:
                    team_image = None
                    try:
                        logging.info("Processing file: '{0}'".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename)))
                        team_image = TeamImage(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), process_id, SQL_CURSOR)
                        products_count = find_product_code_in_db(team_image, 1)
                        team_image.preprocess_image(products_count)
                        logging.info(team_image)
                        #process_exif(os.path.join(IMAGE_FOLDER, filename))
                    except UnicodeEncodeError as ex:
                        logging.error("UnicodeEncodeError captured while processing file: '{0}' Message: {1}".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), repr(ex)))
                    except Exception as ex:
                        logging.error("Exception captured while processing file: '{0}' Message: {1}".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), repr(ex)))

                    if app_config.UPLOAD_FILES == False:
                        logging.warning("Process is set NOT to upload images. UPLOAD_FILES variable is expected to be True.")
                    elif team_image is None:
                        logging.error("File: '{0}' was not processed correctly.".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename)))
                    elif team_image.product_code_from_db is None or len(team_image.product_code_from_db) == 0:
                        logging.error("File: '{0}' was processed but product code was not found in data set".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename)))
                    elif len(team_image.errors) > 0:
                        logging.error("File: '{0}' was processed with errors: '{1}'".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), list_to_str(team_image.errors)))
                    else:
                        #send post with metadata
                        list_of_items = []
                        file_data = {}
                        tile_data = {}
                        items = {}

                        #file_data
                        file_data["product_code"] = team_image.product_code_from_db.upper()
                        file_data["file_name"] = team_image.new_filename
                        file_data["tile_file_name"] = team_image.new_thumbnail_filename
                        file_data["file_size"] = str(os.path.getsize(team_image.processed_filepath))
                        if team_image.filename_image_type == 'JPEG':
                            file_data["mime"] = "jpg"
                        elif team_image.filename_image_type == 'PNG':
                            file_data["mime"] = "png"
                        file_data["width"] = team_image.metadata_image_width
                        file_data["height"] = team_image.metadata_image_height
                        if team_image.filename_is_offer:
                            file_data["category"] = 'offer'
                        elif team_image.filename_is_boxoffer:
                            file_data["category"] = 'boxoffer'
                        elif team_image.filename_arranged:
                            file_data["category"] = 'arranged'
                        else:
                            file_data["category"] = 'undefined'
                        if team_image.logo_removed:
                            file_data["no_logo"] = "Y"
                        else:
                            file_data["no_logo"] = "N"
                        if team_image.filename_is_label:
                            file_data["label"] = "Y"
                        else:
                            file_data["label"] = "N"
                        file_data["DPI"] = str(team_image.metadata_image_dpi)
                        file_data["version"] = str(team_image.filename_image_sequence)
                        if team_image.filename_attributes:
                            attributes = ''
                            for iterator in range(0, len(team_image.filename_attributes)):
                                if team_image.filename_attributes[iterator] is not None and len(team_image.filename_attributes[iterator]) > 0:
                                    if iterator == 0:
                                        attributes += team_image.filename_attributes[iterator]
                                    else:
                                        attributes += '-' + team_image.filename_attributes[iterator]
                            if len(attributes) > 0:
                                file_data["atributes"] = attributes
                            else:
                                file_data["atributes"] = ""
                        list_of_items.append(file_data)
                        #tile_data
                        tile_data["product_code"] = team_image.product_code_from_db.upper()
                        tile_data["file_name"] = team_image.new_thumbnail_filename
                        tile_data["tile_file_name"] = ""
                        tile_data["file_size"] = str(os.path.getsize(team_image.thumbnail_filepath))
                        tile_data["mime"] = "png"
                        tile_data["width"] = int(team_image.metadata_image_width * (app_config.THUMBNAIL_HEIGHT/team_image.metadata_image_height))
                        tile_data["height"] = app_config.THUMBNAIL_HEIGHT
                        tile_data["category"] = 'tile'
                        if team_image.logo_removed:
                            tile_data["no_logo"] = "Y"
                        else:
                            tile_data["no_logo"] = "N"
                        if team_image.filename_is_label:
                            tile_data["label"] = "Y"
                        else:
                            tile_data["label"] = "N"
                        tile_data["DPI"] = str(team_image.metadata_image_dpi)
                        tile_data["version"] = str(team_image.filename_image_sequence)
                        if team_image.filename_attributes:
                            attributes = ''
                            for iterator in range(0, len(team_image.filename_attributes)):
                                if team_image.filename_attributes[iterator] is not None and len(team_image.filename_attributes[iterator]) > 0:
                                    if iterator == 0:
                                        attributes += team_image.filename_attributes[iterator]
                                    else:
                                        attributes += '-' + team_image.filename_attributes[iterator]
                            if len(attributes) > 0:
                                tile_data["atributes"] = attributes
                            else:
                                tile_data["atributes"] = ""
                        list_of_items.append(tile_data)
                        
                        items['items'] = list_of_items
                        json_data = json.dumps(items)

                        token = token_refresh()
                        url0 = app_config.APP_URL + app_config.FILE_UPLOAD_ENDPOINT
                        headers = {"Token": token, "Content-Type": "application/json"}
                        try:
                            r = requests.post(url0, headers=headers, data=json_data)#json=json_data
                            #print(r.text)
                            #print(r.status_code)
                            #print(r.request.headers)
                            if r.status_code >= 200 and r.status_code < 300:
                                logging.info("Metadata for file: '{0}' was uploaded successfully".format(team_image.new_filename))
                            else:
                                logging.error("Status code: '{0}' was returned while sending file's: '{1}' metadata to server. Message {2}".format(r.status_code, team_image.new_filename, repr(re)))
                                continue
                        except requests.exceptions.RequestException as re:
                            logging.error("RequestException was captured while sending file's: '{0}' metadata to server. Message {1}".format(team_image.new_filename, repr(re)))
                            continue
                        except Exception as ex:
                            logging.error("Exception was captured while sending file's: '{0}' metadata to server. Message {1}".format(team_image.new_filename, repr(re)))
                            continue
                        
                        url1 = app_config.APP_URL + app_config.FILE_UPLOAD_ENDPOINT + team_image.new_filename
                        fin = open(team_image.processed_filepath, 'rb')
                        files = {'product_image': fin}
                        try:
                            r = requests.put(url1, headers={'Token' : token}, files=files)
                            #print(r.request.headers)
                            if r.status_code >= 200 and r.status_code < 300:
                                response_dict = json.loads(r.text)
                                if response_dict.get("status") == "200":
                                    logging.info("Image file: '{0}' was uploaded successfully".format(team_image.new_filename))
                                else:
                                    logging.error("Server has processed request but status code: {0} was returned while processing image file: '{1}'".format(response_dict.get("status"), team_image.new_thumbnail_filename, repr(re)))
                            else:
                                logging.error("Status code: '{0}' was returned while uploading file: '{1}' to server.".format(r.status_code, team_image.new_filename))
                                continue
                        except requests.exceptions.RequestException as re:
                            logging.error("RequestException was captured while uploading image file: '{0}' to server. Message {1}".format(team_image.new_filename, repr(re)))
                            continue
                        except Exception as ex:
                            logging.error("Exception was captured while uploading image file: '{0}' to server. Message {1}".format(team_image.new_filename, repr(re)))
                            continue
                        finally:
                            fin.close()
                        
                        tile_file = None
                        try:
                            url2 = app_config.APP_URL + app_config.FILE_UPLOAD_ENDPOINT + team_image.new_thumbnail_filename
                            tile_file = open(team_image.thumbnail_filepath, 'rb')
                            files = {'product_image': tile_file}
                            r = requests.put(url2, headers={'Token' : token}, files=files)
                            if r.status_code >= 200 and r.status_code < 300:
                                response_dict = json.loads(r.text)
                                if response_dict.get("status") == "200":
                                    logging.info("Thumbnail file: '{0}' was uploaded successfully".format(team_image.new_thumbnail_filename))
                                else:
                                    logging.error("Server has processed request but status code: {0} was returned while processing tile file: '{1}'".format(response_dict.get("status"), team_image.new_thumbnail_filename, repr(re)))
                            else:
                                logging.error("Status code: '{0}' was returned while uploading tile file: '{1}' to server".format(r.status_code, team_image.new_thumbnail_filename))
                                continue
                        except requests.exceptions.RequestException as re:
                            logging.error("RequestException was captured while uploading tile file: '{0}' to server. Message {1}".format(team_image.new_thumbnail_filename, repr(re)))
                            continue
                        except Exception as ex:
                            logging.error("Exception was captured while uploading tile file: '{0}' to server. Message {1}".format(team_image.new_thumbnail_filename, repr(re)))
                            continue
                        finally:
                            tile_file.close()
            else:
                move(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), os.path.join(app_config.IMAGE_UNPROCESSED_ERROR_FOLDER, filename))
                logging.warning("File: '{0}' has not allowed extension: '{1}' and has been moved to destination '{2}'. Object will not be processed.".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), os.path.splitext(filename)[-1].lower(), os.path.join(app_config.IMAGE_UNPROCESSED_ERROR_FOLDER, filename)))
        if os.path.isdir(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename)):
            logging.warning("Item: '{0}' is a directory, which is not expected in this location and it was moved to destination: '{1}'. Object will not be processed.".format(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), os.path.join(app_config.IMAGE_UNPROCESSED_ERROR_FOLDER, filename)))
            move(os.path.join(app_config.IMAGE_UNPROCESSED_FOLDER, filename), os.path.join(app_config.IMAGE_UNPROCESSED_ERROR_FOLDER, filename))

    if SQL_CONNECTION is not None:
        if SQL_CURSOR is not None:
            SQL_CURSOR.close()
        SQL_CONNECTION.close()

if __name__ == "__main__":
    full_refresh()