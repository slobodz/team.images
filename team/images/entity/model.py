import os
import re
import cv2
import numpy as np
import imutils
from math import floor
from resizeimage import resizeimage
from PIL import Image

from team.images import logging, app_config

class TeamImage:
    """Class to hold all Team Image data"""
    def __init__(self, file_path, process_id):
        self.file_path = file_path
        self.process_id = process_id
        self.file_size = os.path.getsize(self.file_path)
        self.image_folder, self.file_name = os.path.split(self.file_path)
        self.file_name_no_extension = os.path.splitext(self.file_name)[0].lower()
        self.file_extension = os.path.splitext(self.file_name)[-1].lower()
        self.temp_file_name_no_extension = ""
        self.product_code_from_file_name = ""
        self.possible_product_codes = []
        self.warnings = []
        self.errors = []
        self.products_from_db = []
        self.filename_image_sequence = -1
        self.filename_image_type = ''
        self.filename_logo_removed = False
        self.filename_is_offer = False
        self.filename_is_boxoffer = False
        self.filename_is_label = False
        self.filename_arranged = False
        self.filename_dpi = -1
        self.filename_attributes = []
        self.logo_removed = False
        self.product_code_from_db = ""
        self.exif_dpi = 0
        self.exif_image_description = ''
        self.exif_image_title = ''
        self.exif_image_subject = ''
        self.exif_image_comment = ''
        self.exif_image_keywords = ''
        self.exif_image_author = ''
        self.new_filename = ''
        self.processed_filepath = ''
        self.new_thumbnail_filename = ''
        self.thumbnail_filepath = ''
       
        self.get_metadata_from_image_file()
        self.parse_file_name()         

    def preprocess_image(self, products_count):
        if len(self.metadata_image_format) > 0 and len(self.filename_image_type) > 0 and\
                self.metadata_image_format != self.filename_image_type:
            self.errors.append('FIL: File extension "{0}" and file type "{1}" do not match'\
                .format(self.filename_image_type, self.metadata_image_format))        

        #check DB data
        if products_count == 1:
            if self.product_code_from_file_name.lower() != self.product_code_from_db.lower():
                self.warnings.append('PCE: Product code from file does not match database product code')
            if self.product_code_from_db.find(' ') > -1:
                self.warnings.append('PCE: Product code contain space character')
        #elif products_count > 1:
        #    if len(self.product_code_from_db) > 0:
        #        if self.product_code_from_file_name.lower() != self.product_code_from_db.lower():
        #            self.errors.append('PCE: Product code from file does not match database product code')
            #if self.find_product_code_in_db(self.possible_product_codes, 2) == 0:
            #    if self.find_product_code_in_db(self.possible_product_codes, 3) == 0:
            #        self.find_product_code_in_db(self.possible_product_codes, 4)
        elif products_count == 0: #len(self.product_code_from_db) == 0:
            self.errors.append('PCE: Product code "{0}" was not found in database'\
                .format(self.product_code_from_file_name))

        if app_config.PROCESS_TEMPLATES:
            for template in app_config.TEMPLATES:
                correlation = 0.0
                correlation = self.image_has_template(self.file_path, template)
                #print('Correlation: {0} for template: {1}'.format(correlation, template))
                if correlation >= app_config.CORRELATION_TRESHOLD:
                    #print('Correlation: {0} for template: {1}'.format(correlation, template))
                    self.logo_removed = False
                    break
                else:
                    self.logo_removed = True
            if self.filename_logo_removed != self.logo_removed:
                self.warnings.append('LOG: Filename logo information does not match recorded image logo value')

        if self.filename_dpi > -1 and self.metadata_image_dpi != self.filename_dpi:
            self.errors.append('DPI: Image DPI: {0} does not match filename DPI: {1}'.format(self.metadata_image_dpi, self.filename_dpi))

        if self.filename_is_offer is True and self.filename_is_boxoffer is True:
            self.errors.append('FIL: There are "offer" and "boxoffer" attributes in filename which is not allowed')
        elif self.filename_is_offer is True and self.filename_arranged is True:
            self.errors.append('FIL: There are "offer" and "arr" attributes in filename which is not allowed')
        elif self.filename_is_boxoffer is True\
                and self.filename_arranged is True:
            self.errors.append('FIL: There are "boxoffer" and "arr" attributes in filename which is not allowed')

        self.new_filename = self.create_filename()[0]
        self.new_thumbnail_filename = self.create_filename()[1]
        self.processed_filepath = os.path.join(app_config.IMAGE_PROCESSED_FOLDER, self.new_filename)
        self.thumbnail_filepath = os.path.join(app_config.IMAGE_THUMBNAIL_FOLDER, self.new_thumbnail_filename)

        if len(self.errors) == 0:
            if os.path.isfile(self.processed_filepath):
                #current file already exists in processed folder
                #os.rename(self.file_path, self.processed_filepath + self.process_id)
                #logging.error("File: '{0}' already exists in folder: 'IMAGE_PROCESSED_FOLDER'. It will be saved as:")
                self.errors.append("File: '{0}' already exists in folder: '{1}'".format(self.new_filename, IMAGE_PROCESSED_FOLDER))
            else:
                try:
                    os.rename(self.file_path, self.processed_filepath)
                    #copy2(self.file_path,self.processed_filepath)
                except Exception as ex:
                    self.errors.append("Unable to move file: '{0}' to folder: '{1}'. Message: {2}".format(self.file_path, IMAGE_PROCESSED_FOLDER, repr(ex)))

            if app_config.CREATE_THUMBNAILS is True:
                self.create_thumbnail()

    def create_filename(self):
        """Create file name from attributes"""
        new_filename = ''
        new_thumbnail_filename = ''
        if len(self.product_code_from_db) > 0:
            new_filename += self.product_code_from_db.upper().replace('/', '-')
        else:
            new_filename += self.product_code_from_file_name.upper()
        if self.filename_is_offer or self.filename_is_boxoffer or self.filename_arranged:
            if self.filename_is_offer:
                new_filename += '_offer'
            if self.filename_is_boxoffer:
                new_filename += '_boxoffer'
            if self.filename_arranged:
                new_filename += '_arranged'
        if app_config.PROCESS_TEMPLATES:
            if self.logo_removed:
                new_filename += '_L'
        else:
            if self.filename_logo_removed:
                new_filename += '_L'
        if self.filename_is_label:
            new_filename += '_label'
        if self.filename_dpi > 0:
            new_filename += '_DPI' + str(self.metadata_image_dpi)
        if self.filename_image_sequence > -1:
            if self.filename_image_sequence == 0:
                self.filename_image_sequence += 1
            new_filename += '_v' + str(self.filename_image_sequence).zfill(2)
        new_thumbnail_filename = new_filename
        new_thumbnail_filename += '_Th' + str(app_config.THUMBNAIL_HEIGHT)

        if self.filename_attributes:
            attributes = ''
            for iterator in range(0, len(self.filename_attributes)):
                if self.filename_attributes[iterator] is not None and len(self.filename_attributes[iterator]) > 0:
                    if iterator == 0:
                        attributes += self.filename_attributes[iterator]
                    else:
                        attributes += '-' + self.filename_attributes[iterator]
            if len(attributes) > 0:
                new_filename += '_' + attributes
                new_thumbnail_filename += '_' + attributes

        if self.filename_image_type == 'JPEG':
            new_filename += '.jpg'
        elif self.filename_image_type == 'PNG':
            new_filename += '.png'
        else:
            new_filename += self.file_extension

        if app_config.THUMBNAIL_FORMAT == 'JPEG':
            new_thumbnail_filename += '.jpg'
        elif app_config.THUMBNAIL_FORMAT == 'PNG':
            new_thumbnail_filename += '.png'

        return (new_filename, new_thumbnail_filename)

    def __str__(self):
        STR_SEPARATOR = app_config.STR_SEPARATOR
        return self.file_name + STR_SEPARATOR\
            + str(self.file_size) + STR_SEPARATOR\
            + self.metadata_image_format + STR_SEPARATOR\
            + str(self.metadata_image_width)  + STR_SEPARATOR\
            + str(self.metadata_image_height) + STR_SEPARATOR\
            + str(self.metadata_image_dpi) + STR_SEPARATOR\
            + self.product_code_from_file_name + STR_SEPARATOR\
            + list_to_str(self.possible_product_codes) + STR_SEPARATOR\
            + str(self.filename_logo_removed) + STR_SEPARATOR\
            + str(self.filename_is_boxoffer) + STR_SEPARATOR\
            + str(self.filename_is_offer) + STR_SEPARATOR\
            + str(self.filename_is_label) + STR_SEPARATOR\
            + str(self.filename_arranged) + STR_SEPARATOR\
            + str(self.filename_dpi) + STR_SEPARATOR\
            + str(self.logo_removed) + STR_SEPARATOR\
            + str(self.filename_image_sequence) + STR_SEPARATOR\
            + self.product_code_from_db + STR_SEPARATOR\
            + self.new_filename + STR_SEPARATOR\
            + list_to_str(self.products_from_db) + STR_SEPARATOR\
            + list_to_str(self.warnings) + STR_SEPARATOR\
            + list_to_str(self.errors)

    def get_metadata_from_image_file(self):
        """Populate Image metadata from file"""
        try:
            image_file = Image.open(self.file_path)
            self.metadata_image_format = image_file.format
            self.metadata_image_width, self.metadata_image_height = image_file.size
            self.metadata_image_dpi = DEFAULT_DPI
            if image_file.info.get('dpi'):
                x_dpi, y_dpi = image_file.info['dpi']
                if x_dpi == y_dpi and x_dpi >= app_config.MIN_DPI:
                    self.metadata_image_dpi = x_dpi
                elif x_dpi == y_dpi and x_dpi > 0 and x_dpi < MIN_DPI:
                    self.errors.append('DPI: Image DPI is set too low: {0}'.format(x_dpi))
                else:
                    self.warnings.append('DPI: Metadata DPI information is not consistent [x_dpi=' + str(x_dpi)
                                         + ', y_dpi = ' + str(y_dpi) + ']. Default value will be used.')
                    if x_dpi > y_dpi and x_dpi >= app_config.DEFAULT_DPI:
                        image_file.save(image_path, dpi=(x_dpi, x_dpi))
                    elif y_dpi > x_dpi and y_dpi >= app_config.DEFAULT_DPI:
                        image_file.save(image_path, dpi=(y_dpi, y_dpi))
                    else:
                        image_file.save(image_path, dpi=(app_config.DEFAULT_DPI, app_config.DEFAULT_DPI))
            else:
                self.warnings.append('DPI: Metadata does not contain DPI information. Default value will be used.')
                image_file.save(image_path, dpi=(app_config.DEFAULT_DPI, app_config.DEFAULT_DPI))
        except Exception as ex:
            exc_type = ex.__class__.__name__
            self.errors.append("IMG: Unable to process image [" + self.file_name + "] Exception Type: " + str(exc_type) + " Error: " + str(ex))
        finally:
            if image_file is not None:
                image_file.close()

    def create_thumbnail(self):
        """Create thumbnail(s) for provided image"""
        try:
            image_file = Image.open(self.image_path)
            #for tile_height in THUMBNAIL_HEIGHT:
            #    for tile_format in THUMBNAIL_FORMAT:
            thumbnail = resizeimage.resize_height(image_file, app_config.THUMBNAIL_HEIGHT)
            thumbnail.save(self.thumbnail_path)
        except Exception as ex:
            exc_type = ex.__class__.__name__
            self.errors.append("IMG: Unable to create thumbnail image [" + self.file_name
                               + "] Exception Type: " + str(exc_type) + " Error: " + str(ex))
        finally:
            if image_file is not None:
                image_file.close()

    def parse_file_name(self):
        """Get image attrubutes from file name"""
        self.temp_file_name_no_extension = self.file_name_no_extension
        if self.temp_file_name_no_extension.find('box_back_offer') > -1:
            self.temp_file_name_no_extension = \
                self.temp_file_name_no_extension.replace('box_back_offer', '_boxoffer_') #_boxbackoffer_
        elif self.temp_file_name_no_extension.find('box_front_offer') > -1:
            self.temp_file_name_no_extension = self.temp_file_name_no_extension.replace('box_front_offer', '_boxoffer_')#_boxfrontoffer_
        elif self.temp_file_name_no_extension.find('box_offer') > -1:
            self.temp_file_name_no_extension = self.temp_file_name_no_extension.replace('box_offer', '_boxoffer_')
        elif self.temp_file_name_no_extension.find('box') > -1:
            self.errors.append('FIL: File attribute "box" is not allowed.')
            #self.temp_file_name_no_extension = self.temp_file_name_no_extension.replace('box', '_boxoffer_')

        if self.file_extension == '.png':
            self.filename_image_type = 'PNG'
        elif self.file_extension == '.jpg' or self.file_extension == '.jpeg':
            self.filename_image_type = 'JPEG'
        #elif self.file_extension == '.gif':
        #    self.filename_image_type = 'GIF'
        else:
            self.errors.append('EXT: File extension "{0}" is not suported.'.format(self.file_extension))

        image_name_splitted = self.temp_file_name_no_extension.split('_')
        self.product_code_from_file_name = image_name_splitted[0].upper()

        #self.possible_product_codes.append(self.product_code_from_file_name)
        #if(self.product_code_from_file_name.find('-') > -1):
        #    self.possible_product_codes.append(rreplace(self.product_code_from_file_name, '-', '/', 1))
        self.possible_product_codes = self.get_all_possible_product_codes(self.product_code_from_file_name)

        image_name_splitted.remove(image_name_splitted[0])
        for part in image_name_splitted:
            part = part.strip()
            part = part.replace('copy', '')
            part = part.replace('app', '')
            #part = part.replace('arr', '')
            part = part.replace('ar', 'arr')
            part = part.replace('kopia', '')
            part = part.replace(' - ', '')
            part = part.replace('(1)', '')
            part = part.replace('(2)', '')
            part = part.replace('(3)', '')
            part = part.replace('old', '01')
            #part = part.replace('etap', '')
            part = part.strip()
            if len(part) > 0:
                processed_attribute = False
                if part == 'l' or part == 'll':
                    self.filename_logo_removed = True
                    processed_attribute = True
                elif part == 'boxoffer':  #get info about box offer
                    self.filename_is_boxoffer = True
                    processed_attribute = True
                elif part == 'offer':
                    self.filename_is_offer = True
                    processed_attribute = True
                elif part == 'offerl':
                    self.filename_is_offer = True
                    self.filename_logo_removed = True
                    processed_attribute = True
                elif part == 'label':
                    self.filename_is_label = True
                    processed_attribute = True
                elif part == 'arr':
                    self.filename_arranged = True
                    processed_attribute = True
                elif (len(part) == 1 and re.match(r'[0-9]', part)) \
                    or (len(part) == 2 and re.match(r'[0-9][0-9]', part)): #integer
                    self.filename_image_sequence = int(part)
                    processed_attribute = True
                elif (len(part) == 2 and re.match(r'[0-9]l', part)) \
                    or (len(part) == 3 and re.match(r'[0-9][0-9]l', part)) \
                    or (len(part) == 3 and re.match(r'[0-9]-l', part)) \
                    or (len(part) == 4 and re.match(r'[0-9][0-9]-l', part)):
                    self.filename_logo_removed = True
                    self.filename_image_sequence = int(part.replace('l', '').replace('-', ''))
                    processed_attribute = True
                elif part.find('dpi') > -1:
                    dpi = part.replace('dpi', '')
                    if (len(dpi) == 2 and re.match(r'[0-9][0-9]', dpi)) \
                        or (len(dpi) == 3 and re.match(r'[0-9][0-9][0-9]', dpi)) \
                        or (len(dpi) == 4 and re.match(r'[0-9][0-9][0-9][0-9]', dpi)):
                        self.filename_dpi = int(dpi)
                        processed_attribute = True
                elif (len(part) == 2 and re.match(r'[0-9]a', part)) \
                    or (len(part) == 3 and re.match(r'[0-9][0-9]a', part)):
                    self.filename_image_sequence = int(part.replace('a', ''))
                    processed_attribute = True
                elif len(part) == 3 and re.match(r'v[0-9][0-9]', part):
                    self.filename_image_sequence = int(part.replace('v', ''))
                    processed_attribute = True

                if not processed_attribute:
                    self.filename_attributes.append(part)
                    #self.warnings.append('ATR: Attribute ' + part + ' was not processed')
        return

    def get_all_possible_product_codes(self, product_code):
        """Tries to guess similar product codes"""
        split_char = '-'
        possible_product_codes = list()
        possible_product_codes.append(product_code)
        if product_code.find('-') > -1:
            possible_product_codes.append(rreplace(product_code, '-', '/', 1))

        product_code_splitted = product_code.split(split_char)
        code_chunks = len(product_code_splitted)
        if code_chunks > 0:
            last_chunk = product_code_splitted[code_chunks - 1]
            if (len(last_chunk) == 1 and re.match(r'[0-9]', last_chunk)) \
                or (len(last_chunk) == 2 and re.match(r'[0-9][0-9]', last_chunk)):
                new_code = ''
                new_code_short = ''
                for x in range(0, code_chunks):
                    if len(product_code_splitted[x].strip()) > 0:
                        if x == 0:
                            new_code = product_code_splitted[x]
                        elif x > 0 and x < code_chunks - 1:
                            new_code = new_code + '-' + product_code_splitted[x]
                        else:
                            new_code_short = new_code
                            new_code = new_code + '/' + product_code_splitted[x]
                possible_product_codes.append(new_code)
                if len(new_code_short) > 0:
                    possible_product_codes.append(new_code_short)

        #KALORIK
        possible_product_codes_2 = list()
        for code in possible_product_codes:
            if code.find('-KALORIK') > -1:
                possible_product_codes_2.append(code.replace('-KALORIK', ''))
            else:
                possible_product_codes_2.append(code + '-KALORIK')

        for code_2 in possible_product_codes_2:
            possible_product_codes.append(code_2)

        product_code_splitted_space = product_code.split(' ')
        if len(product_code_splitted_space) > 1 and len(product_code_splitted_space[0]) >= 4:
            possible_product_codes.append(product_code_splitted_space[0])
            if product_code_splitted_space[0].find('-KALORIK') > -1:
                possible_product_codes.append(code.replace('-KALORIK', ''))
            else:
                possible_product_codes.append(code + '-KALORIK')

        #SCHOTT
        possible_product_schott1 = list()
        for code_schott1 in possible_product_codes:
            if code_schott1.find('-SCHOTT') > -1:
                possible_product_schott1.append(code_schott1.replace('-SCHOTT', ''))
            else:
                possible_product_schott1.append(code_schott1 + '-SCHOTT')

        for code_schott in possible_product_schott1:
            possible_product_codes.append(code_schott)

        product_code_splitted_space_shott = product_code.split(' ')
        if len(product_code_splitted_space_shott) > 1 and len(product_code_splitted_space_shott[0]) >= 4:
            possible_product_codes.append(product_code_splitted_space_shott[0])
            if product_code_splitted_space_shott[0].find('-SCHOTT') > -1:
                possible_product_codes.append(code.replace('-SCHOTT', ''))
            else:
                possible_product_codes.append(code + '-SCHOTT')

        #add all codes
        possible_product_codes = list(set(possible_product_codes))
        possible_product_codes.sort(key=len, reverse=True)
        return possible_product_codes

    def image_has_template(self, image_path, template_path):
        has_template = False

        # load the image image, convert it to grayscale, and detect edges
        template = cv2.imread(template_path)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template = cv2.Canny(template, 50, 200)
        (tH, tW) = template.shape[:2]
        #cv2.imshow("Template", template)

        # load the image, convert it to grayscale, and initialize the
        # bookkeeping variable to keep track of the matched region
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        found = (0, (0, 0), 0)

        # loop over the scales of the image
        for scale in np.linspace(0.01, 1.0, 200)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(gray, width=int(gray.shape[1] * scale))
            r = gray.shape[1] / float(resized.shape[1])

            # if the resized image is smaller than the template, then break
            # from the loop
            if resized.shape[0] < tH or resized.shape[1] < tW:
                break

            # detect edges in the resized, grayscale image and apply template
            # matching to find the template in the image
            edged = cv2.Canny(resized, 50, 200)
            result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF_NORMED)
            (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)

            # check to see if the iteration should be visualized
            if app_config.VISUALIZE:
                # draw a bounding box around the detected region
                clone = np.dstack([edged, edged, edged])
                cv2.rectangle(clone, (maxLoc[0], maxLoc[1]),
                              (maxLoc[0] + tW, maxLoc[1] + tH), (0, 0, 255), 2)
                cv2.imshow("Visualize", clone)
                cv2.waitKey(0)

            # if we have found a new maximum correlation value, then ipdate
            # the bookkeeping variable
            if found is None or maxVal > found[0]:
                found = (maxVal, maxLoc, r)
            #print(found[0], maxVal)
        # unpack the bookkeeping varaible and compute the (x, y) coordinates
        # of the bounding box based on the resized ratio
        if found is not None:
            (_, maxLoc, r) = found
            (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
            (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))

            # draw a bounding box around the detected result and display the image
            #cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
            #cv2.imshow("Image", image)
            if found[0] >= app_config.CORRELATION_TRESHOLD:
                has_template = True
                #print(found[0])
        #else:
        #    print(found = [0])
        #return has_template
        return found[0]
#End of TeamImage class