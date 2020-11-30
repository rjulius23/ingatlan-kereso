#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# External dependencies
import pprint
import traceback
import requests  #
from time import sleep
from lxml import html
from lxml import etree  # html pretty print
from urllib.parse import quote
from urllib.request import urlopen  # URL encoding
from datetime import datetime  # formatted time
import json


# Internal dependencies
from ingatlan_kereso_secrets import *  # import secret keys


pp = pprint.PrettyPrinter(indent=4)

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-language": "en-US,en;q=0.9,hu;q=0.8",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
}


def get_apartment_ids(url):
    print("GET {}".format(url))

    page = requests.get(url, headers=HEADERS)
    tree = html.fromstring(page.content)

    apartments_count = tree.xpath("//div[@class='results__number']")
    count = apartments_count[0].get("data-listings-count")
    count = count.replace(" ", "")
    pagecount = int((int(count) / 20)) + 1
    print("COUNT {} - PAGECOUNT {}".format(count, pagecount))

    apartmentIds = []

    # First page parsing
    apartmentButtonInfoList = tree.xpath(
        "//button[@class='listing__action--hide button--link js-show-or-hide-listing']"
    )
    for apartmentButtonInfo in apartmentButtonInfoList:
        apartmentId = apartmentButtonInfo.get("data-id")
        apartmentIds.append(apartmentId)

    parsed_page_count = 1

    while parsed_page_count != pagecount:

        page_index = parsed_page_count + 1
        next_page_url = url + "?page=" + str(page_index)
        # print("GET {}".format(next_page_url))

        nextpage_apartment_ids = get_apartments_for_nextpages(next_page_url)
        apartmentIds += nextpage_apartment_ids

        # print(apartmentIds)

        parsed_page_count += 1

    print("Found apartments: " + str(len(apartmentIds)))
    print("---")

    return apartmentIds


def get_apartments_for_nextpages(url):
    # print("GET {}".format(url))

    page = requests.get(url, headers=HEADERS)
    tree = html.fromstring(page.content)
    apartmentButtonInfoList = tree.xpath(
        "//button[@class='listing__action--hide button--link js-show-or-hide-listing']"
    )

    next_apartmentIds = []
    for apartmentButtonInfo in apartmentButtonInfoList:
        apartmentId = apartmentButtonInfo.get("data-id")
        next_apartmentIds.append(apartmentId)

    return next_apartmentIds


#   apartment_type = lakas / haz
def get_apartment_details(apartment_id):

    apartment_details = []

    apartment_url = "https://ingatlan.com/" + str(apartment_id)

    apartment_page = requests.get(apartment_url, headers=HEADERS)
    apartment_tree = html.fromstring(apartment_page.content)

    # collect data

    apartment_detailed_type = (
        apartment_tree.xpath("//div[@class='listing-subtype']")[0]
        .text_content()
        .encode("latin1")
        .decode("utf8")
    )
    apartment_detailed_type = apartment_detailed_type.split(" ")[1]

    apartment_title = (
        apartment_tree.xpath("//h1[@class='js-listing-title']")[0]
        .text_content()
        .encode("latin1")
        .decode("utf8")
    )

    apartment_parameters = apartment_tree.xpath(
        "//div[@class='paramterers']/table/tr/td/text()"
    )
    apartment_description = (
        apartment_tree.xpath("//div[@class='long-description']")[0]
        .text_content()
        .encode("latin1")
        .decode("utf8")
    )

    apartment_size = None
    apartment_area_size = None
    apartment_rooms = None
    apartment_price = None

    parameter_values = apartment_tree.xpath("//span[@class='parameter-value']")
    parameter_values_len = len(parameter_values)

    if parameter_values_len == 3:

        apartment_size = (
            apartment_tree.xpath("//span[@class='parameter-value']")[0]
            .text_content()
            .encode("latin1")
            .decode("utf8")
        )
        apartment_size = apartment_size.split(" ")[0]

        apartment_rooms = (
            apartment_tree.xpath("//span[@class='parameter-value']")[1]
            .text_content()
            .encode("latin1")
            .decode("utf8")
        )
        apartment_rooms = apartment_rooms[:6]
        apartment_rooms = apartment_rooms.replace(" ", "")

        apartment_price = (
            apartment_tree.xpath("//span[@class='parameter-value']")[2]
            .text_content()
            .encode("latin1")
            .decode("utf8")
        )
        apartment_price = apartment_price.split(" ")[0]
        apartment_price = apartment_price.replace(",", ".")

    elif parameter_values_len == 4:

        apartment_size = (
            apartment_tree.xpath("//span[@class='parameter-value']")[0]
            .text_content()
            .encode("latin1")
            .decode("utf8")
        )
        apartment_size = apartment_size.split(" ")[0]

        apartment_area_size = (
            apartment_tree.xpath("//span[@class='parameter-value']")[1]
            .text_content()
            .encode("latin1")
            .decode("utf8")
        )
        apartment_area_size = apartment_area_size.split(" ")[0]

        apartment_rooms = (
            apartment_tree.xpath("//span[@class='parameter-value']")[2]
            .text_content()
            .encode("latin1")
            .decode("utf8")
        )
        apartment_rooms = apartment_rooms[:6]
        apartment_rooms = apartment_rooms.replace(" ", "")

        apartment_price = (
            apartment_tree.xpath("//span[@class='parameter-value']")[3]
            .text_content()
            .encode("latin1")
            .decode("utf8")
        )
        apartment_price = apartment_price.split(" ")[0]
        apartment_price = apartment_price.replace(",", ".")

    else:
        print(
            "ERROR - invalid parameter-value count: "
            + str(parameter_values_len)
            + " id: "
            + apartment_id
        )

    # fill data
    apartment_details.append(apartment_id)
    apartment_details.append(apartment_url)
    apartment_details.append(apartment_title)
    apartment_details.append(apartment_size)
    apartment_details.append(apartment_area_size)
    apartment_details.append(apartment_rooms)
    apartment_details.append(apartment_price)

    # Process apartment extra parameters
    apartment_params_keys = apartment_parameters[::2]
    apartment_params_vals = apartment_parameters[1::2]
    apartment_params = dict(zip(apartment_params_keys, apartment_params_vals))

    default_no_text = u"nincs adat"

    apartment_state = (
        apartment_params.get(u"Ingatlan \xc3\xa1llapota", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_comfor = (
        apartment_params.get(u"Kil\xc3\xa1t\xc3\xa1s", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_floor = (
        apartment_params.get("Emelet", default_no_text).encode("latin1").decode("utf8")
    )
    apartment_floors = (
        apartment_params.get(u"\xc3\x89p\xc3\xbclet szintjei", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_elevat = (
        apartment_params.get("Lift", default_no_text).encode("latin1").decode("utf8")
    )
    apartment_height = (
        apartment_params.get(u"Belmagass\xc3\xa1g", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_heatin = (
        apartment_params.get(u"F\xc5\xb1t\xc3\xa9s", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )

    # Optional for 'lakas'
    apartment_garden = (
        apartment_params.get("Kertkapcsolatos", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_access = (
        apartment_params.get(u"Akad\xc3\xa1lymentes\xc3\xadtett", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_bathro = (
        apartment_params.get(u"F\xc3\xbcrd\xc5\x91 \xc3\xa9s WC", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_view = (
        apartment_params.get(u"Kil\xc3\xa1t\xc3\xa1s", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_parkin = (
        apartment_params.get(u"Parkol\xc3\xa1s", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_costs = (
        apartment_params.get(u"Rezsik\xc3\xb6lts\xc3\xa9g", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_compas = (
        apartment_params.get(u"T\xc3\xa1jol\xc3\xa1s", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_topflo = (
        apartment_params.get(u"Tet\xc5\x91t\xc3\xa9r", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_erkely = (
        apartment_params.get(u"Erk\xc3\xa9ly", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_aircon = (
        apartment_params.get(u"L\xc3\xa9gkondicion\xc3\xa1l\xc3\xb3", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )
    apartment_parkco = (
        apartment_params.get(u"Parkol\xc3\xb3hely \xc3\xa1ra", default_no_text)
        .encode("latin1")
        .decode("utf8")
    )

    # Parameters for 'haz'

    # Add data
    apartment_details.append(apartment_state)  # ingatlan allapota
    apartment_details.append(apartment_detailed_type)  # ingatlan tipusa
    apartment_details.append(apartment_comfor)  # komfort
    apartment_details.append(apartment_floor)  # emelet
    apartment_details.append(apartment_floors)  # epulet szintei
    apartment_details.append(apartment_elevat)  # lift
    apartment_details.append(apartment_height)  # belmagassag
    apartment_details.append(apartment_heatin)  # futes
    apartment_details.append(apartment_costs)  # rezsikoltseg
    apartment_details.append(apartment_access)  # akadalymentesitett
    apartment_details.append(apartment_bathro)  # Furdo/WC
    apartment_details.append(apartment_compas)  # tajolas
    apartment_details.append(apartment_view)  # kilatas
    apartment_details.append(apartment_garden)  # kertkapcsolatos
    apartment_details.append(apartment_topflo)  # tetoter
    apartment_details.append(apartment_parkin)  # parkolas
    apartment_details.append(apartment_parkco)  # parkolohely ara
    apartment_details.append(apartment_erkely)  # erkely
    apartment_details.append(apartment_aircon)  # klima

    apartment_details.append(apartment_description)  # reszletes leiras

    return apartment_details


def get_distance_to_work(from_place):

    to_place = quote(WORK_PLACE)
    from_place_full = "Budapest," + quote(from_place)
    request_url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json?origins="
        + from_place_full
        + "&destinations="
        + to_place
        + "&mode=transit&key="
        + GOOGLE_MAPS_DISTANCE_MATRIX_API_KEY
    )
    r = requests.get(url=request_url)

    transit_time = 0
    try:
        transit_time = r.json()["rows"][0]["elements"][0]["duration"]["value"]
    except Exception:
        print("EXCEPTION - GoogleMaps cannot handle this place: " + from_place)

    transit_time = int(transit_time / 60)

    return transit_time


def insert_new_row(wks, apartment_details, first_empty_row_index):

    apartment_id = apartment_details[0]

    print("INSERT " + apartment_id + " to Row " + str(first_empty_row_index))

    apartment_url = apartment_details[1]
    apartment_title = apartment_details[2]
    apartment_traveltime = get_distance_to_work(from_place=apartment_title)
    apartment_size = apartment_details[3]
    apartment_area_size = apartment_details[4]
    apartment_rooms = apartment_details[5]
    apartment_price = apartment_details[6]
    apartment_state = apartment_details[7]  # ingatlan állapota
    apartment_detailed_type = apartment_details[8]  # ingatlan tipusa
    apartment_confort = apartment_details[9]  # komfort
    apartment_floor = apartment_details[10]  # emelet
    apartment_floors = apartment_details[11]  # epulet szintei
    apartment_elevator = apartment_details[12]  # lift
    apartment_height = apartment_details[13]  # belmagassag
    apartment_heating = apartment_details[14]  # futes
    apartment_livingcost = apartment_details[15]  # rezsikoltseg
    apartment_accessibility = apartment_details[16]  # akadalymentesitett
    apartment_bathroom = apartment_details[17]  # Furdo/WC
    apartment_compass = apartment_details[18]  # tajolas
    apartment_view = apartment_details[19]  # kilatas
    apartment_garden = apartment_details[20]  # kertkapcsolatos
    apartment_topfloor = apartment_details[21]  # tetoter
    apartment_parking = apartment_details[22]  # parkolas
    apartment_parkingcost = apartment_details[23]  # parkolohely ara
    apartment_erkely = apartment_details[24]  # erkely
    apartment_aircon = apartment_details[25]  # klima

    apartment_description = apartment_details[26]  # Reszletes leiras

    creation_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    apartment_status = "Aktiv, UJ"

    row_values = [
        apartment_id,
        apartment_status,
        apartment_url,
        apartment_title,
        apartment_traveltime,
        apartment_size,
        apartment_area_size,
        apartment_rooms,
        apartment_price,
        apartment_detailed_type,
        apartment_state,
        apartment_confort,
        apartment_floor,
        apartment_floors,
        apartment_elevator,
        apartment_height,
        apartment_heating,
        apartment_livingcost,
        apartment_accessibility,
        apartment_bathroom,
        apartment_compass,
        apartment_view,
        apartment_garden,
        apartment_topfloor,
        apartment_parking,
        apartment_parkingcost,
        apartment_erkely,
        apartment_aircon,
        apartment_description,
        creation_date,
    ]

    wks.update_row(index=first_empty_row_index, values=row_values, col_offset=0)

    sleep(3)


def get_deleted_apartments(
    db_apartment_ids, db_activity_column, ingatlan_apartment_ids_array
):

    deleted_apartments = []

    iterator = 0

    for db_apartment_id in db_apartment_ids:

        # get Activity for the db_apartment
        activity_column_element = db_activity_column[iterator]
        iterator += 1

        isAlreadyDeleted = False

        if activity_column_element == "Nem aktiv":
            isAlreadyDeleted = True

        db_apartment_id_exists = False

        for ingatlan_apartment_id in ingatlan_apartment_ids_array:

            if ingatlan_apartment_id == db_apartment_id:
                db_apartment_id_exists = True

        # Add deleted apartment if it doesn't exist in Ingatlan results and not yet marked as deleted
        if db_apartment_id_exists == False and isAlreadyDeleted == False:
            deleted_apartments.append(db_apartment_id)

    return deleted_apartments


def mark_deleted_apartments(wks, deleted_apartments, db_apartment_ids):

    print("Mark deleted apartments")
    pp.pprint(deleted_apartments)

    deletion_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    for deleted_apartment_id in deleted_apartments:

        # Search for deleted_apartment_index
        deleted_apartment_index = 0
        iterator = 1
        found_the_deleted_apartment = False
        for db_apartment_id in db_apartment_ids:

            iterator += 1

            if db_apartment_id == deleted_apartment_id:
                deleted_apartment_index = iterator
                found_the_deleted_apartment = True

        # Mark apartment as deleted
        if found_the_deleted_apartment == True:
            print(
                "Mark "
                + str(deleted_apartment_id)
                + " as deleted (row="
                + str(deleted_apartment_index)
                + ")..."
            )
            wks.update_cell("B" + str(deleted_apartment_index), "Nem aktiv")
            wks.update_cell("AB" + str(deleted_apartment_index), deletion_date)

        else:
            print(
                "ERROR - cannot find a deleted apartment index: "
                + str(deleted_apartment_id)
            )


def main():
    apt_ids = get_apartment_ids(
        url="https://ingatlan.com/listar/elado+haz+csak-kepes+45-150-mFt+95-m2-felett+ar-szerint"
    )
    apt_details = []
    for apt_id in apt_ids:
        apt_details.append(get_apartment_details(apt_id))

    print(apt_details[0])
    print(len(apt_details))


if __name__ == "__main__":
    main()