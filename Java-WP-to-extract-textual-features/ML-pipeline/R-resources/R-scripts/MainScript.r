
args <- commandArgs(trailingOnly = TRUE)
base_folder2 <- args[1]
trainingSetDirectory2 <- args[2]
testSetDirectory2  <- args[3]

# @author sebastiano panichella

#install packages if not installed yet
print("We install packages if not installed yet")
if (!require(tm)){ install.packages("tm") }
if (!require(stringr)){ install.packages("stringr") } 
if (!require(stopwords)){ install.packages("stopwords") }
if (!require(slam)){ install.packages("slam") }
if (!require(snakecase)){ install.packages("snakecase") }
if (!require(data.table)){ install.packages("data.table") }
if (!require(XML)){ install.packages("XML") }

#load the libraries...
print("We load the libraries")
library(tm)
library(stringr)
library(stopwords)
library(slam)

base_folder <- "C:/workspace/MasterThesis/Java-WP-to-extract-textual-features/ML-pipeline/R-resources/R-scripts"   

if(!is.na(base_folder2))
{
  base_folder<- base_folder2
  print("1) argument \"docs_location\" used in R by setwd() ")
}

setwd(base_folder)

source("./utilities.R")
#path software artifacts
trainingSetDirectory <- "./documents/training"
testSetDirectory <- "./documents/test"


if(!is.na(trainingSetDirectory2) && !is.na(testSetDirectory2) )
{
  trainingSetDirectory<- trainingSetDirectory2
  testSetDirectory<- testSetDirectory2
  print("2) argument \"trainingSetDirectory\" given as argumet to the R script ")
  print("3) \"testSetDirectory\" given as argumet to the R script ")
  }

#dir.create(simplifiedOracle_path, showWarnings = FALSE, recursive = TRUE)

# creating folders with pre-processed documents (e.g., camel case splitting, etc.)
print("-> CREATING folders with pre-processed documents")
trainingSetDirectory_preprocessed <- "./documents-preprocessed/trainingSetDirectory"
testSetDirectory_preprocessed <- "./documents-preprocessed/testSetDirectory"

# files where the matrices of training and test sets will be stored with all orcale information
print("-> STORING files concerning the matrices of training and test sets will all oracle information in the last column")
tdm_full_trainingSet_with_oracle_info_path <- "./documents-preprocessed/tdm_full_trainingSet_with_oracle_info.csv"
tdm_full_testSet_with_oracle_info_path <- "./documents-preprocessed/tdm_full_testSet_with_oracle_info.csv"
tdm_full_with_oracle_info_path <- "./documents-preprocessed/tdm_full_with_oracle_info.csv"

# we preprocess files
#pre_processing(trainingSetDirectory, trainingSetDirectory_preprocessed, ".txt")
#pre_processing(testSetDirectory, testSetDirectory_preprocessed, ".txt")
#-> check if the directory need to be cleaned before nex step
print("---> PREPROCESSING Training and Test Sets files ")
pre_processing(trainingSetDirectory, trainingSetDirectory_preprocessed)
pre_processing(testSetDirectory, testSetDirectory_preprocessed)

# directories to index
#print("directories with files to index")
directories <- c(trainingSetDirectory_preprocessed, testSetDirectory_preprocessed)

# the following command index the software artifacts
# and store this data in "tm" (it is a sparse matrix)
tdm <- build_tm_matrix(directories)
print("---> CREATING Sparse Term-by-Document-Matrix from Training and Test Sets files ")

# extract only the interesting part of the matrix
Training_files <- list.files(trainingSetDirectory, recursive=TRUE)
TestSet_files <- list.files(testSetDirectory, recursive=TRUE)

#we obtain the full term by document matrics
print("---> we obtain the full term by document matrics")
tdm_full <- as.matrix(tdm)
tdm_full<- t(tdm_full)
print("---> Created Non-Sparse Term-by-Document-Matrix from Training and Test Sets files ")

tdm_full_trainingSet <- tdm_full[Training_files,]
tdm_full_testSet <- tdm_full[TestSet_files,]

#FINAL PART: we finally add oracle information to the csv files
print("---FINAL PART: we add oracle information to the Term-by-Document-Matrix")
tdm_full_trainingSet_with_oracle_info<- as.data.frame(tdm_full_trainingSet)
tdm_full_testSet_with_oracle_info<- as.data.frame(tdm_full_testSet)

temp1<- rep("",length(tdm_full_trainingSet_with_oracle_info[,1]))
temp2<- rep("",length(tdm_full_testSet_with_oracle_info[,1]))

tdm_full_trainingSet_with_oracle_info<- cbind(tdm_full_trainingSet_with_oracle_info,temp1)
tdm_full_testSet_with_oracle_info<- cbind(tdm_full_testSet_with_oracle_info,temp2)

colnames(tdm_full_trainingSet_with_oracle_info)[length(tdm_full_trainingSet_with_oracle_info[1,])] <- "safety"
colnames(tdm_full_testSet_with_oracle_info)[length(tdm_full_testSet_with_oracle_info[1,])] <- "safety"


print("WRITING the CSV files (uuseful for WEKA) of training and test sets with the oracle information")
write.csv(tdm_full_trainingSet_with_oracle_info,tdm_full_trainingSet_with_oracle_info_path)
write.csv(tdm_full_testSet_with_oracle_info,tdm_full_testSet_with_oracle_info_path)

