NAF-HeidelTime provides a NAF wrapper around heideltime-standalone for Dutch and English.

DISCLAIMER: This is a preliminary implementation which allows HeidelTime to be included in a NAF-pipeline for Dutch. An alternative version that will integrate HeidelTime better in the pipeline (avoiding to call TreeTagger) is currently under development.

Please report problems with the code to: antske.fokkens@vu.nl


This module makes use of third party software. Please make sure you respect the licenses and citation requirements imposed by each.

Please note that heideltime-standalone is provided under the GNU GPL v3 license.
More information on Heideltime can be found here: https://code.google.com/p/heideltime/
If you use this module, make sure to respect the citation requirements mentioned on the HeidelTime page.


Prerequisites:

HeidelTime standalone uses TreeTagger, which is freely available, but may not be redistributed.
Treetagger can be found here:

http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/

Make sure to install TreeTagger for the correct operating system and to include all files required for tagging Dutch or English (depending on the language you're working with)


The wrapper makes use of the VU KafNaf parser:

https://github.com/cltl/KafNafParserPy

Please make sure the version of this parser is up to date.


Running HeidelTime through the wrapper:

Preparation:

0. Make sure all prerequisites are available on your machine
1. Make sure that the path to treetagger is set in config.props
2. The file config.props should be present in the directory from which the wrapper is called
3. If the KafNafParser is not installed, you can adapt the following line in HeidelTime_NafKaf.py:

\#sys.path.append('')

a) add the path to the KafNafParser between the quotes
b) uncomment the code line (by removing the #)

You can now run the module as follows

cat inputfile.naf | python PATH-TO-HEIDELTIME/HeidelTime_NafKaf.py PATH-TO-HEIDELTIME/heideltime-standalone/ tmp/ > outputfile.naf

where tmp/ can be the path to any scratch directory where you can temporarily write and read files.


