#!/usr/bin/env python

from subprocess import call
import sys
import shutil
import os
import time
import re
from lxml import etree

#sys.path.append('')
from KafNafParserPy import *
#mapping language marking from naf to options in HeidelTime (NewsReader languages only)
#FIXME: for now English only, Dutch is default
langOptions = {'en': 'ENGLISH'}

def create_raw_text(inputtext):
    """
    reads in file and returns entire content as string
    """
    raw_text = ''
  
    myin = open(inputtext, 'r')
    for line in myin:
        raw_text += line


    return raw_text


def get_all_time_tokens(my_timeElements):
    """Function that retrieves the text from a list of xml elements"""
    time_strings = []
    for time in my_timeElements:
        time_strings.append(time.text)

    return time_strings


def tokens_only_dates(time, alltimes, text):
    """Function that checks if same tokens also occur when not a date (unlikely given regex setup of HeidelTime)"""
    
    occurrences = text.count(time)
    
    identified_as_time = alltimes.count(time)
   
    
    if occurrences == identified_as_time:
        return True
    elif occurrences > identified_as_time:
        #FIXME: this is a hack, we should also look at punctuation, etc
        occurrences = time.count(time + ' ')
        if occurrences > identified_as_time:
            return False
        else:
            return True
    elif identified_as_time > occurrences:
        #FIXME: should be proper printed error
        print >> sys.stderr, 'Error: this string occurs more often as time expression than it occurs'
        
        return True


def remove_punctuation(tokenText):
    """
        Additional cleanup to deal with differences in tokenization. Removes punctuation markers at the end of a string
    """
    tokenText = tokenText.rstrip('.')
    tokenText = tokenText.rstrip(',')
    tokenText = tokenText.rstrip(';')
    tokenText = tokenText.rstrip('?')
    tokenText = tokenText.rstrip(')')
    tokenText = tokenText.rstrip(':')
    tokenText = tokenText.rstrip('"')
    tokenText = tokenText.rstrip('/')
    tokenText = tokenText.rstrip('(')
    return tokenText



def retrieve_token_identifiers(times, nafobject):
    """
        Goes through identified time objects and maps each time object to the first sequence of tokens it matches in the token layer of naf and retrieves their identifiers. Creates a list where time object and span form one item.
    """
    #outcome stored in list, dictionary would not preserve the order
    timeSpans = []
    #time expressions will be mapped to tokens (conversion to terms later if applicable)
    textTokens = nafobject.get_tokens()
    
    #keeping track of what we need to find
    timeIndex = 0
    currentTE = times[timeIndex]
    teTokens = currentTE.text.split()
    cTok = teTokens.pop(0)
    
    #keeping track of what we have found
    span = []
    found = []
    for token in textTokens:
        tokenText = token.get_text()
        tokenText = remove_punctuation(tokenText)
        if tokenText == cTok or (cTok in tokenText and '-' in tokenText):
            span.append(token.get_id())
            if len(teTokens) == 0:
                #done with this time expression
                timeSpans.append([currentTE,span])
                timeIndex += 1
                if len(times) - 2 < timeIndex:
                    #completely done
                    break
                else:
                    #reset other values
                    currentTE = times[timeIndex]
                    teTokens = currentTE.text.split()
                    cTok = teTokens.pop(0)
                    span = []
                    found = []
            else:
                #add the token just found as track record
                found.append(cTok)
                cTok = teTokens.pop(0)
        elif found:
            #if we have elements in found and the next token is not matching, we do not
            #have a full match, reset original search
            
            #reset teTokens, cTok, found and span
            teTokens = found + [cTok] + teTokens
            cTok = teTokens.pop(0)
            found = []
            span = []
    return timeSpans

def update_timecounts(tList):
    """
        Checks for tokens in time expressions if they are also tokens in larger time expression. Adds such tokens to identification list
    """
    
    compList = tList
    updatedList = []
    checked = []
    for t in tList:
        updatedList.append(t)
        #only update once
        if not t in checked:
            for ct in compList:
                #we want an extra copy of t for every time expression t is a subset of
                if t != ct and t in ct:
                    updatedList.append(t)
                    checked.append(t)
    return updatedList


def checkFirstLine(lines):
    for line in lines:
        if '<?xml version="1.0"?>' in line:
            return True
        else:
            return False


def check_and_clean_timetext(timetext):
    """
        If heideltime is problems with the text it prints out debugging information, making the output not valid as XML.
        Additional function that checks whether this is the case and
        """
    mytext = open(timetext, 'r')
    lines = mytext.readlines()
    mytext.close()
    #only replace text if debugging remarks printed before
    if not checkFirstLine(lines):
        new_text = ''
        xmlStarted = False
        for line in lines:
            if '<?xml version="1.0"?>' in line:
                xmlStarted = True
            if xmlStarted:
                new_text += line
        outtext = open(timetext, 'w')
        outtext.write(new_text)



def time_expressions_are_always_timeexpression(my_times, raw_text):
    '''
        Checks whether there are any identified time expressions that also occur as non-time expressions.
    '''
    time_strings = get_all_time_tokens(my_times)
    
    raw_text = re.sub('<[^>]*>', '', raw_text)
    
   
    
    #create list of time strings
    my_timeStrings = []
    for time in my_times:
        timestring = time.text
        my_timeStrings.append(timestring)
    
    #dealing with cases where one time expression is a subset of another
    #multiplying entries of shorter time if that is the case
    
    my_timeStrings = update_timecounts(my_timeStrings)

    allTEs = True
    for timestring in time_strings:
        if not tokens_only_dates(timestring, my_timeStrings, raw_text):
            allTEs = False
    return allTEs





def addTimexLayer(timeSpans, nafobject, term=False):
    """
        Takes a list of timex-expressions and the ids of tokens of that span the expression as input and adds a timex layer to naf
    """
    
    for termSpan in timeSpans:
        timex = termSpan[0]
        span = termSpan[1]
        nafTime = Ctime()
        #add basic features
        timeId = timex.get('tid').replace('t','tmx')
        nafTime.set_id(timeId)
        nafTime.set_type(timex.get('type'))
        nafTime.set_value(timex.get('value'))
        
        #create Span
        nafSpan = Cspan()
        nafSpan.create_from_ids(span)

        #addSpan to time
        nafTime.set_span(nafSpan)

        #add time to nafobject
        nafobject.add_timex(nafTime)


def update_kafornaffile(timextext, nafobject, logfile, inputfile, skipFirstDate):
    """
    It goes through a text marked up by heideltime, identifies spans of found times and
        adds them to timeExpressions.
    """
    #collect basic components
    try:
        my_timex = etree.parse(timextext,etree.XMLParser(remove_blank_text=True))
        raw_text = create_raw_text(timextext)
        my_times = my_timex.findall('TIMEX3')
        
        if skipFirstDate:
            #remove first timex which dct and not a token
            my_times.pop(0)
    
        #add timex layer (should also be there if not terms are found)
    
        nafobject.timex_layer = CtimeExpressions()
        nafobject.root.append(nafobject.timex_layer.get_node())
        
        #don't do all this if the text does not contain time expressions
        if my_times:
            if time_expressions_are_always_timeexpression(my_times, raw_text):
                timeSpans = retrieve_token_identifiers(my_times, nafobject)
            
                addTimexLayer(timeSpans, nafobject)
            else:
            #FIXME: given that HeidelTime works with regex, this should not happen, but you never know....
                logout = open(logfile, 'a')
                logout.write('Possible mismatch between occurrence and timespans for document: ' + inputfile + '\n')
                logout.close()
    except:
        copyname = timextext + '-failed'
        shutil.copy(timextext,copyname)
#       logout = open(logfile, 'a')
# logout.write('Could not parse xml file coming out of: ' + inputfile + '\n')


def create_heideltime_output(tmpdir, raw_text, heideldir, lang='DUTCH'):
    """
    Writes out raw text in tmpfile, passes it through Heideltime and writes the output in another tmpfile
    """
    
    #raw_text = '<![CDATA[' + raw_text + ']]>'
    mytemptext = open(tmpdir + '/inputtext', 'w')
    mytemptext.write(raw_text.encode('utf8'))
    mytemptext.close()
    heideltimejar = heideldir + 'de.unihd.dbs.heideltime.standalone.jar'
    
    my_call = ['java','-jar', heideltimejar, '-l', lang,tmpdir + '/inputtext']
    f = open(tmpdir + '/outputtext', 'w')
    call(my_call, stdout=f)
    f.close()
    check_and_clean_timetext(tmpdir + '/outputtext')


def process_text_with_heideltime(inputfile, heideldir, tmpdir, outdir = ''):
    '''Function that takes an inputfile in naf and a temporary directory as input. Retrieves text from NAF, passes it throuh heideltime and adds a timex layer'''
    
    #obtain begintime

    
    begintime = time.strftime('%Y-%m-%dT%H:%M:%S%Z')
    obj = KafNafParser(inputfile)
    dct = obj.header.get_dct()
    skipFirstDate = False
    if dct is not None:
        docNormDate = dct.split('T')[0]
        dateParts = docNormDate.split('-')
        myDate = dateParts[2] + '-' + dateParts[1] + '-' + dateParts[0] + '\n'
        skipFirstDate = True
    else:
        myDate = ''
    
    raw_text = obj.get_raw()
    #also retrieve document creation time from NAF
    
    if not raw_text:
        
        raw_text = ''
        textTokens = obj.get_tokens()
        noFollowSpace = True
        for tokenObj in textTokens:
            token = tokenObj.get_text()
            if token in ['.',',',';',':','?',')'] or noFollowSpace:
                raw_text += token
                noFollowSpace = False
            else:
                raw_text += ' ' + token
            if token in ['(','-']:
                noFollowSpace = True
        
    #set language for HeidelTime depending on doc's language
    lang = obj.root.get('{http://www.w3.org/XML/1998/namespace}lang')
    if lang in langOptions:
        lang = langOptions.get(lang)
    else:
        lang = 'DUTCH'
    
    date_raw_text = myDate + raw_text
    create_heideltime_output(tmpdir, date_raw_text, heideldir, lang)

    logFile = tmpdir + '/log'
    update_kafornaffile(tmpdir + '/outputtext', obj, logFile, inputfile, skipFirstDate)

    lp = Clp(name="heideltime",version="standalone-1.7",btimestamp=begintime)
    obj.add_linguistic_processor('timex3', lp)


    if outdir:
        nafFilename = inputfile.split('/')[-1]
        obj.dump(outdir + '/' + nafFilename)
    else:
        obj.dump()


def initiate_processing(input, heideldir, tmpdir, outdir = ''):
    """
        Checks whether input is directory, if so processes all files in directory.
        Else processes file. OLD FUNCTION NOT USED IN STDIN VERSION
    """
    
    if os.path.isdir(input):
        for myfile in os.listdir(input):
            #FIXME: 1. we also want to be able to do raw text
            #FIXME: 2. we should try to process any file and catch exception if fails
            if myfile.endswith('naf') or myfile.endswith('kaf') or myfile.endswith('xml'):
                inputfile = input + '/' + myfile
                process_text_with_heideltime(inputfile, heideldir, tmpdir, outdir)
    else:
        process_text_with_heideltime(input, heideldir, tmpdir, outdir)


def main(argv=None):

    if argv == None:
        argv = sys.argv

    inputfile = sys.stdin
    if len(argv) < 3:
        print >> sys.stderr, 'Error: the path to heideltime and tmpdir must be provided'
    elif len(argv) < 4:
        process_text_with_heideltime(inputfile, argv[1], argv[2])
    else:
        process_text_with_heideltime(inputfile, argv[1], argv[2], argv[3])


if __name__ == '__main__':
    main()
