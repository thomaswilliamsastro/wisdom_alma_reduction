#!/bin/bash

# This script runs on Linux and MaxOS and downloads all the selected files to the current working directory in up to 5 parallel download streams.
# Should a download be aborted just run the entire script again, as partial downloads will be resumed. Please play nice with the download systems
# at the ARCs and do not increase the number of parallel streams.

# connect / read timeout for wget / curl
export TIMEOUT_SECS=300
# how many times do we want to automatically resume an interrupted download?
export MAX_RETRIES=3
# after a timeout, before we retry, wait a bit. Maybe the servers were overloaded, or there was some scheduled downtime.
# with the default settings we have 15 minutes to bring the dataportal service back up.
export WAIT_SECS_BEFORE_RETRY=300
# the files to be downloaded
LIST=("
https://almascience.nrao.edu/dataPortal/2017.1.00904.S_uid___A001_X1296_X5bd_auxiliary.tar
https://almascience.nrao.edu/dataPortal/2015.1.01572.S_uid___A001_X2fb_X8f3_auxiliary.tar
https://almascience.nrao.edu/dataPortal/2017.1.00904.S_uid___A002_Xc6ff69_X52d.asdm.sdm.tar
https://almascience.nrao.edu/dataPortal/2016.2.00046.S_uid___A001_X124a_X233_auxiliary.tar
https://almascience.nrao.edu/dataPortal/2015.1.01572.S_uid___A002_Xb60be4_X20db.asdm.sdm.tar
https://almascience.nrao.edu/dataPortal/member.uid___A001_X2fb_X8f3.README.txt.tar
https://almascience.nrao.edu/dataPortal/member.uid___A001_X124a_X233.README.txt.tar
https://almascience.nrao.edu/dataPortal/member.uid___A001_X1296_X5bd.README.txt.tar
https://almascience.nrao.edu/dataPortal/2016.2.00046.S_uid___A002_Xc2d675_X98f.asdm.sdm.tar
")
# If we terminate the script using CTRL-C during parallel downloads, the remainder of the script is executed, asking if
# the user wants to unpack tar files. Not very nice. Exit the whole script when the user hits CTRL-C.
trap "exit" INT

# quickly log in to the server (if required) and create a cookies file. This is because some users are using shared machines for long-running
# downloads where the credentials can be seen in plain-text in the task list.
function start_session {
  local username=anonymous
  export authentication_status=0
  if [ "${username}" != "anonymous" ]; then
    # only prompt for the password again if we haven't already. What could be going on here? The servers
    # have been restarted and the local cookie file is no longer valid.
    if [ -z ${password} ]; then
      echo ""
      echo -n "Please enter the password for ALMA account ${username}: "
      read -s password
      echo ""
      export password
    fi

    if command -v "curl" > /dev/null 2>&1; then
      login_command=(curl -s -k -o /dev/null -c alma-rh-cookie.txt --fail "-u" "${username}:${password}")
    elif command -v "wget" > /dev/null 2>&1; then
      login_command=(wget --quiet --delete-after --no-check-certificate --auth-no-challenge --keep-session-cookies --save-cookies alma-rh-cookie.txt "--http-user=${username}" "--http-password=${password}")
    fi
    # echo "${login_command[@]}" "https://almascience.nrao.edu/dataPortal/login"
    $("${login_command[@]}" "https://almascience.nrao.edu/dataPortal/login")
    authentication_status=$?
    if [ $authentication_status -eq 0 ]; then
      echo "	    OK: credentials accepted."
    else
      echo "	    ERROR: login failed. Error code is ${authentication_status}"
    fi
  fi
}
export -f start_session

# clean up the cookies file after downloading is complete
function end_session {
	# Included unset variable: password, for ticket : ICT-16332
	unset password
	rm -fr alma-rh-cookie.txt
}
export -f end_session

export failed_downloads=0

# download a single file.
# attempt the download up to N times
function dl {
  local file=$1
  local filename=$(basename $file)
  # the nth attempt to download a single file
  local attempt_num=0

  # wait for some time before starting - this is to stagger the load on the server (download start-up is relatively expensive)
  sleep $[ ( $RANDOM % 10 ) + 2 ]s

  if command -v "curl" > /dev/null 2>&1; then
    local tool_name="curl"
    local download_command=(curl -C - -S -s -k -O -f -b alma-rh-cookie.txt --speed-limit 1 --speed-time ${TIMEOUT_SECS})
  elif command -v "wget" > /dev/null 2>&1; then
    local tool_name="wget"
    local download_command=(wget -c -q -nv --no-check-certificate --auth-no-challenge --load-cookies alma-rh-cookie.txt --timeout=${TIMEOUT_SECS} --tries=1)
  fi

  # manually retry downloads. 
  # I know wget and curl can both do this, but curl (as of 10.04.2018) will not allow retry and resume. I want consistent behaviour so 
  # we implement the retry mechanism ourselves.
  echo "starting download of $filename"
  until [ ${attempt_num} -ge ${MAX_RETRIES} ]
  do
    # echo "${download_command[@]}" "$file"
    $("${download_command[@]}" "$file")
    status=$?
    # echo "status ${status}"
    if [ ${status} -eq 0 ]; then
      echo "	    successfully downloaded $filename"
      break
    else
      failed_downloads=1
      # users requested a string instead of a simple exit code - attempt to make it look like the curl output
      if [ ${status} -eq 8 ] && [ ${tool_name} = "wget" ]; then 
        echo "wget: (8) Server issued an error response."
      elif [ ${status} -eq 4 ] && [ ${tool_name} = "wget" ]; then
        echo "wget: (4) Network failure."
      elif { [ ${status} -eq 6 ] && [ ${tool_name} = "wget" ]; } || { [ ${status} -eq 22 ] && [ ${tool_name} = "curl" ]; }; then
        # if we restart the servers then our cookies are invalidated
        end_session
        echo "authentication error - retrying the login"
        start_session
        if [ $authentication_status -eq 0 ]; then
          # our retry attempt was hampered by a credentials issue. We shouldn't count this as an attempt. Give a bonus try...
          echo "		resuming download of $filename, still attempt $[${attempt_num}+1]"
          $("${download_command[@]}" "$file")
        fi
      fi
      #echo "${login_command[@]}" "https://almascience.nrao.edu/dataPortal/login"
      echo $("${download_command[@]}" "$file/client/status/$status")

      echo "		download $filename was interrupted with error code ${tool_name}/${status}"
      attempt_num=$[${attempt_num}+1]
      if [ ${attempt_num} -ge ${MAX_RETRIES} ]; then
        echo "	  ERROR giving up on downloading $filename after ${MAX_RETRIES} attempts  - rerun the script manually to retry."
      else
        echo "		download $filename will automatically resume after ${WAIT_SECS_BEFORE_RETRY} seconds"
        sleep ${WAIT_SECS_BEFORE_RETRY}
        echo "		resuming download of $filename, attempt $[${attempt_num}+1]"
      fi
    fi
  done
}
export -f dl

tars_exist=0
invalid_tars_exist=0
function check_integrity {
	for nextfile in ${LIST}; do
		tarname=$( basename ${nextfile} )
		if [[ ${nextfile} =~ ^.*\.tar$ ]] && [ -f ${tarname} ]; then
			tars_exist=1
			tar tf ${tarname} >/dev/null 2>&1
			tar_corrupted=$?
			if [[ ${tar_corrupted} -eq 1 ]]; then
				echo "tar invalid: ${tarname}"
				invalid_tars_exist=1
				break
			fi
		fi
	done
	if [[ ${invalid_tars_exist} -eq 1 ]]; then
		echo ""
		echo "Some of the downloads unfortunately failed. Please re-run the download script again in a few hours and, if this still fails, submit a ticket to the ALMA Helpdesk"
	fi
}

function unpack_tars {
	echo ""
	# override TIMEOUT so we never time-out. These files may take days to download. It's annoying if the user comes back
	# to the terminal after a weekend and finds that they weren't quick enough to automatically untar the files.
	# That's a pretty big timeout. One year in seconds.
	read -p "All files have been downloaded successfully. Should they be untarred? [y/n] " -n 1 -r -t 31449600
	echo ""
	if [[ ${REPLY} =~ ^[Yy]$ ]]; then
		for nextfile in ${LIST}; do
			if [[ ${nextfile} =~ ^.*\.tar$ ]]; then
				tarname=$( basename ${nextfile} )
				echo "	    unpacking ${tarname}"
				tar xf ${tarname}
			fi
		done
	fi
}

# temporary workaround for ICT-13558: "xargs -I {}" fails on macos with variable substitution where the length of the variable
# is greater than 255 characters. For the moment we download these long filenames in serial. At some point I'll address this issue
# properly, allowing parallel downloads.
# Array of filenames for download where the filename > 251 characters
# 251? Yes. The argument passed to bash is "dl FILENAME;" In total it cannot exceed 255. So FILENAME can only be 251
export long_files=()
# arrayf of filenames with length <= 255 characters - can be downloaded in parallel.
export ok_files=()
function split_files_list {
	for nextfile in ${LIST}; do
		length=${#nextfile}
		if [[ $length -ge 251 ]]; then
			long_files+=($nextfile)
		else
			ok_files+=($nextfile)
		fi
	done
}

# Main body
# ---------

# check that we have one of the required download tools
if ! (command -v "wget" > /dev/null 2>&1 || command -v "curl" > /dev/null 2>&1); then
   echo "ERROR: neither 'wget' nor 'curl' are available on your computer. Please install one of them.";
   exit 1
fi

echo "Downloading the following files in up to 5 parallel streams. Total size is 23.2GB."
echo "${LIST}"
echo "In case of errors each download will be automatically resumed up to 3 times after a 5 minute delay"
echo "To manually resume interrupted downloads just re-run the script."
# tr converts spaces into newlines. Written legibly (spaces replaced by '_') we have: tr "\_"_"\\n"
# IMPORTANT. Please do not increase the parallelism. This may result in your downloads being throttled.
# Please do not split downloads of a single file into multiple parallel pieces.

# Included for retrials of passwords, for ticket : ICT-16332
export RETRY_ATTMPTS=3

while [ $RETRY_ATTMPTS -gt 0 ];
do
	start_session
	if [ $authentication_status -eq 0 ]; then
		RETRY_ATTMPTS=0
    else
		end_session
		RETRY_ATTMPTS=$(( $RETRY_ATTMPTS - 1 ))
    fi
done

start_session
if [ $authentication_status -eq 0 ]; then
	echo "your downloads will start shortly...."
	split_files_list
	# "dl" is a function for downloading. I abbreviated the name to leave more space for the filename
	echo ${ok_files[@]} | tr \  \\n | xargs -P5 -n1 -I '{}' bash -c 'dl {}; end_session {};'
	for next_file in ${long_files[@]}; do
		dl ${next_file}
	done
fi
end_session
check_integrity
if [ $failed_downloads -eq 0 ] && [ $tars_exist -eq 1 ] && [ $invalid_tars_exist -eq 0 ]; then
	unpack_tars
fi
echo "Done."
