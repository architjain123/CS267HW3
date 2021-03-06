<?php
// submitted by Archit, Damanpreet and Inderpreet

namespace hw3\termprep;

use seekquarry\yioop\library\Library;
use seekquarry\yioop\library\PhraseParser;
use seekquarry\yioop\library\FetchUrl;
use seekquarry\yioop\library\processors\HtmlProcessor;
use seekquarry\yioop\library\CrawlConstants;

require_once "vendor/autoload.php";
Library::init();

// cli agruments
$file = $argv[1];
$locale = $argv[2];

// read urls from file
$lines = file($file) or die("ERROR: $file not found.");
if(empty($lines)){
    die("ERROR: $file is empty.");
}

// trim urls and create urls array
$urls = [];
foreach ($lines as $line) {
    $url[CrawlConstants::URL] = trim($line);
    array_push($urls, $url);
}

// download urls and get page content
$pages = FetchUrl::getPages($sites = $urls);
$html_processor = new HtmlProcessor($max_description_len = 20000, $summarizer_option = CrawlConstants::CENTROID_WEIGHTED_SUMMARIZER);

mkdir("temp");
$i = 0;
foreach ($pages as $page){
    // in case some pages do not return content
    if (trim($page[CrawlConstants::PAGE]) == ""){
        $failed_url = $page[CrawlConstants::URL];
        print_r("WARNING: Cannot process $failed_url as page is empty. SKIPPING.");
        print_r("\n");
        continue;
    }

    // get page content
    $html_content = $html_processor->process($page[CrawlConstants::PAGE], $page[CrawlConstants::URL]);
    $page_locale = $html_content[CrawlConstants::LANG];
    $page_text = PhraseParser::extractWordStringPageSummary($html_content);
    $page_text_terms = explode(" ", $page_text);
    
    // get unique terms
    $unique_terms = [];
    foreach($page_text_terms as $term){
        $unique_terms[$term] = true;
    }

    $keys = array_keys($unique_terms);

    // do not need to stem in case locale is none
    if ($locale == "none"){
        $stemmed_keys = $keys;
    }
    else{
        // stem and print the keys
        $stemmed_keys = [];
        foreach($keys as $key){
            $stemmed_key = PhraseParser::stemTerms($key, $locale);
            if (count($stemmed_key) > 0){
                array_push($stemmed_keys, $stemmed_key[0]);
            }
        }
    }
    
    sort($stemmed_keys);
    create_summary_file($i, $stemmed_keys);
    $i = $i + 1;
    print_r($page[CrawlConstants::URL]);
    foreach($stemmed_keys as $key){
        print_r($key . "\n");
    }
    print_r("\n");
}

// put the content in a file which can be used to compute tfidf scores
function create_summary_file($i, $stemmed_keys){
    $text = implode(" ", $stemmed_keys);
    file_put_contents("temp/$i.txt", $text);
}
?>