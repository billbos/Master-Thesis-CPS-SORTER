
if (!require(snakecase)){ install.packages("snakecase") }
if (!require(data.table)){ install.packages("data.table") }
if (!require(XML)){ install.packages("XML") }
if (!require(dplyr)){ install.packages("dplyr") } 

#pre_processing <- function(input, output, format){
# input<- trainingSetDirectory
# output<- trainingSetDirectory_preprocessed
pre_processing <- function(input, output){
  files <- list.files(input, recursive=TRUE)
  
  dir.create(output, showWarnings = FALSE, recursive = TRUE)
  for (document in files){
    #if (endsWith(document, format)){
       #print(document)
      #text <- scan(paste(input, document, sep="/"), what = character())
      con <- file(paste(input, document, sep="/"), "r")
      text<- readLines(con) # empty
      close(con)
      text <- to_sentence_case(text)
      #text <- gsub("[[:punct:]]", " ", text)
      #text <- gsub("username", "user name", text)
      #new_file <- extract_file_name(document)
      write.table(text, paste(output, document, sep="/"), row.names = FALSE, col.names = FALSE)
    #}
  }
}

extract_file_name <- function(document){
  tokens <- str_split(document, "/")
  n_tokens <- length(tokens[[1]]) 
  if (n_tokens > 1){
    last_token <- tokens[[1]][n_tokens]
    return(last_token)
  } else {
    return(document)
  }
}

build_tm_matrix <- function(folders){
  corpus <- SimpleCorpus(DirSource(folders, encoding = "UTF-8"), control = list(language = "en"))
  corpus <- tm_map(corpus, stripWhitespace) # remove white spaces
  corpus <- tm_map(corpus, removeNumbers)   # remove numbers
  corpus <- tm_map(corpus, removePunctuation) # remove punctuation
  corpus <- tm_map(corpus, content_transformer(tolower)) # transform everything to lower case
  
  # Apply stopword lists
  corpus <- tm_map(corpus, removeWords, stopwords("en")) 
  corpus <- tm_map(corpus, removeWords, stopwords::stopwords(language = "en", source = "smart"))
  corpus <- tm_map(corpus, removeWords, stopwords::stopwords(language = "en", source = "snowball"))
  corpus <- tm_map(corpus, removeWords, stopwords::stopwords(language = "en", source = "stopwords-iso"))
  corpus <- tm_map(corpus, removeWords, c("apache", "getter", "setter", "mysql", "print", "substr", "regex", "javax", "extend", "enum", "code", "common", "button", "array", "bean", "jdbc", "source", "com", "function", "serial", "stack", "thrown", "yes", "true", "false", "string", "str", "org", "null", "abstract", "assert","boolean","break","byte", "case","catch","char","continue","default","do","double","else","enum","extends","final","finally","float","for","if","implements","import","instanceof","int","interface","long","native","new","package","private","protected","public","return","short","static","strictfp","super","syncronized","this","throw","throws","transient","try","void","volatile","while","goto","const","java", "class", "import","github", "http", "html", "for", "while", "then", "private", "public", "protected", "try", "catch","instead","https","http","href","ibm","throw","throws","clone","javadoc","bug", "string","method","list","array","object","println","char","obj","junit","switch","case","javadoc","args"))
  
  # Applying stemming
  corpus <- tm_map(corpus, stemDocument, language = "english")
  
  # Build the document-by-term matrix
  tdm <- TermDocumentMatrix(corpus, control = list(stemming = TRUE, wordLengths = c(2,Inf), bounds = list(global=c(2,Inf))))
  
  # Apply tf-idf weighting schema
  tdm2 <- weightSMART(tdm, "ntn")
  
  return(tdm2)
}

get_parent_folder <- function(document){
  tokens <- str_split(document, "/")
  n_tokens <- length(tokens[[1]]) 
  if (n_tokens > 1){
    parent <- paste(tokens[[1]][1:(n_tokens-1)],collapse = "/")
    return(parent)
  } else {
    return(parent)
  }
}



