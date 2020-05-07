package org.zhaw.ch.R_Tm_package;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
 

public class TermByDocumentCreation {

	public static void main(String[] args) {
		// TODO Auto-generated method stub

		//local path to the R script "MainScript.r"
		String pathRScript = "/Users/panc/Desktop/Zurich-applied-Science/Collaborations/UZH/master-students/Bill-bosshard/ECLIPSE/workspace/ML-pipeline/R-resources/R-scripts/MainScript.r";
	
		// here are located the "documents" folder and the  "utilities.R script"
		String docs_location = "/Users/panc/Desktop/Zurich-applied-Science/Collaborations/UZH/master-students/Bill-bosshard/ECLIPSE/workspace/ML-pipeline/R-resources/R-scripts/";

		// locations of training and test sets
		String documentsTrainingSet = "/Users/panc/Desktop/Zurich-applied-Science/Collaborations/UZH/master-students/Bill-bosshard/ECLIPSE/workspace/ML-pipeline/R-resources/R-scripts/documents/1-use_cases";
		String documentsTestSet = "/Users/panc/Desktop/Zurich-applied-Science/Collaborations/UZH/master-students/Bill-bosshard/ECLIPSE/workspace/ML-pipeline/R-resources/R-scripts/documents/4-class_description";
		
		//command to execute
		String command = "/usr/local/bin/Rscript "+ pathRScript+" "+docs_location+ " "+documentsTrainingSet+ " "+documentsTestSet+" ";// path of command "/usr/local/bin/Rscript" identified using: "which Rscript" from command line
		
		//we print the command to execute
		System.out.println(" \n \n Executing command (considering R script and arguments): \n "+command+" \n");
		System.out.println("R script and arguments: ");
		System.out.println("- base_folder2 <- args[1] ");
		System.out.println("- trainingSetDirectory2 <- args[2]  ");
		System.out.println("- testSetDirectory2  <- args[3] ");
		System.out.println("- simplifiedOracle2_path  <- args[4]  \n");
		
		System.out.println("Rscript running  \n");
		// -- Linux/Mac osx --
		try {
		    //Process process = Runtime.getRuntime().exec("ls /Users/panc/Desktop");
			Process process = Runtime.getRuntime().exec(command);
			 
		    BufferedReader reader = new BufferedReader(
		            new InputStreamReader(process.getInputStream()));
		    String line;
		    while ((line = reader.readLine()) != null) {
		        System.out.println(line);
		    }	    
		 
		    reader.close();
		 
		} catch (IOException e) {
		    e.printStackTrace();
		}
	}

}
