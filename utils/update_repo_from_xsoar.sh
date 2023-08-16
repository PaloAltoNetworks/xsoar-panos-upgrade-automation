###
# update_repo_from_xsoar.sh
# This script updates all the content in this repository from a given XSOAR server.
##

RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
ENDCOLOR="\e[0m"


DOWNLOAD_DIRECTORY="$PWD/Packs/AllCustomContent"
PACK_DIRECTORY="$PWD/Packs/PAN_OS_Upgrade_Services"

function check_deps() {
  if ! command -v demisto-sdk &> /dev/null
  then
      echo -e "${RED}demisto-sdk not found or not installed. Are you in a virtual environment?${ENDCOLOR}"
      exit
  fi
}

function make_directory() {
  # Create the download directory, which stores all the content.
  if [ -d $DOWNLOAD_DIRECTORY ]
  then
    echo -e "${YELLOW}Directory already exists. Removing directory ${DOWNLOAD_DIRECTORY}.${ENDCOLOR}"
    rm -rf $DOWNLOAD_DIRECTORY
  fi

  echo -e "${GREEN}Creating directory${ENDCOLOR}"
  mkdir $DOWNLOAD_DIRECTORY
  return 0
}

function download() {
  if [ -z $DEMISTO_API_KEY ]
  then
    echo "Specify Demisto API key: "
    read DEMISTO_API_KEY
  fi
  if [ -z DEMISTO_BASE_URL ]
  then
    echo "Specify XSOASR Base URL (ex. 'https://1.1.1.1'): "
    read DEMISTO_BASE_URL
  fi
  echo -e "${YELLOW}Downloading all files using the demisto-sdk...${ENDCOLOR}"
  demisto-sdk download --insecure -a -o $DOWNLOAD_DIRECTORY -f
  return 0
}

function copy_to_pack_directory() {
  echo -e "${YELLOW}Copying files to Pack directory: ${PACK_DIRECTORY}${ENDCOLOR}"
  cd $DOWNLOAD_DIRECTORY
  for line in `egrep -r "Network Operations|Assurance" */* | awk -F: '{print $1}' | sort | uniq | grep -v Integrations | grep -v Scripts` ; do cp $line ../PAN_OS_Upgrade_Services/$line ; done
  return 0
}

make_directory
if [ $? -ne 0 ]
then
  echo -e "${RED}Directory creation failed.${ENDCOLOR}"
  exit 1
fi

download
if [ $? -ne 0 ]
then
  echo -e "${RED}Download Failed${ENDCOLOR}"
  exit 1
fi

copy_to_pack_directory