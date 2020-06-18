package org.zhaw.ch.ml;
import weka.core.Attribute;
import weka.core.Instance;
import weka.core.Instances;
import weka.core.converters.ArffSaver;
import weka.core.converters.CSVLoader;
import weka.core.converters.ConverterUtils.DataSource;
import weka.classifiers.trees.J48;
import weka.classifiers.trees.RandomForest;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map.Entry;
import java.util.Random;
import java.util.StringJoiner;
import java.util.stream.Collectors;

import weka.classifiers.Classifier;
import weka.classifiers.Evaluation;
import weka.classifiers.bayes.NaiveBayes;
import weka.classifiers.functions.Logistic;

public class WekaClassifier extends MachineLearningClassifier {

	public WekaClassifier() {
		classifierToolChain = "Weka";
		
		
	}

	
	public static Instances merge(Instances data1, Instances data2)
		    throws Exception
		{
		    // Check where are the string attributes
		    int asize = data1.numAttributes();
		    boolean strings_pos[] = new boolean[asize];
		    for(int i=0; i<asize; i++)
		    {
		        Attribute att = data1.attribute(i);
		        strings_pos[i] = ((att.type() == Attribute.STRING) ||
		                          (att.type() == Attribute.NOMINAL));
		    }

		    // Create a new dataset
		    Instances dest = new Instances(data1);
		    dest.setRelationName(data1.relationName() + "+" + data2.relationName());

		    DataSource source = new DataSource(data2);
		    Instances instances = source.getStructure();
		    Instance instance = null;
		    while (source.hasMoreElements(instances)) {
		        instance = source.nextElement(instances);
		        dest.add(instance);

		        // Copy string attributes
		        for(int i=0; i<asize; i++) {
		            if(strings_pos[i]) {
		                dest.instance(dest.numInstances()-1)
		                    .setValue(i,instance.stringValue(i));
		            }
		        }
		    }

		    return dest;
		}

	static List<Classifier> getClassifiers(){
		List<Classifier> classifiers = new ArrayList<Classifier>();
		Classifier j48 = new J48();
		Classifier naiveBayes = new NaiveBayes();
		Classifier logistic = new Logistic();
		Classifier randomForest = new RandomForest();
		classifiers.addAll(Arrays.asList(j48, naiveBayes, logistic, randomForest));
		return classifiers;
	}
	static void trainClassifier(Instances training, List<Classifier> classifiers){
		classifiers.stream().forEach(cls -> {try {
			cls.buildClassifier(training);
		} catch (Exception e) {
			e.printStackTrace();
		}});
	}
	
	static List<String> saveClassifier(Instances training, List<Classifier> classifiers, String output){
		List<String> outputPaths = new ArrayList<String>();
		classifiers.stream().forEach(cls -> {try {
			cls.buildClassifier(training);
			String outputPath = output + "/"+ cls.getClass().getSimpleName() + ".model";
			weka.core.SerializationHelper.write(outputPath, cls);
			outputPaths.add(outputPath);
		} catch (Exception e) {
			e.printStackTrace();
		}});
		return outputPaths;
	}
	
	
	static Classifier loadClassifier(String modelOutput) throws Exception {
		Classifier cls = (Classifier) weka.core.SerializationHelper.read(modelOutput);
		return cls;
	}
	
	static void csvToArff(String input_file, String output_file) throws IOException{
		 // load CSV
	    CSVLoader loader = new CSVLoader();
	    loader.setSource(new File(input_file));
	    Instances data = loader.getDataSet();

	    // save ARFF
	    ArffSaver saver = new ArffSaver();
	    saver.setInstances(data);
	    saver.setFile(new File(output_file));
	    saver.writeBatch();
	    // .arff file will be created in the output location
	}

	
	static List<String> evaluateClassifier(Instances training, Instances test, Instances balanced, List<Classifier> classifiers, String filename) throws Exception{
	System.out.println("Starting....");
	List<String> results = new ArrayList<String>(); 
	// evaluate classifier and print some statistics
	classifiers.stream().forEach(cls -> {
		try {
			StringJoiner row = new StringJoiner(","); 
			row.add(cls.getClass().getSimpleName());
			row.add(filename);
			
			Evaluation eval = new Evaluation(training);
			eval.evaluateModel(cls, training);
			row.add(String.valueOf(eval.pctCorrect()));
			
			Evaluation evalt = new Evaluation(training);
			evalt.evaluateModel(cls, test);
			row.add(String.valueOf(evalt.pctCorrect()));
			
			Evaluation b_eval = new Evaluation(training);
			b_eval.evaluateModel(cls, balanced);
			row.add(String.valueOf(b_eval.pctCorrect()));

			Instances entire_set =  merge(training,test);
			Evaluation cross_eval = new Evaluation(entire_set);
			cross_eval.crossValidateModel(cls, entire_set , 10, new Random(1));
			row.add(String.valueOf(cross_eval.pctCorrect()));

			row.add(String.valueOf(evalt.precision(0)));
			row.add(String.valueOf(evalt.precision(1)));
			row.add(String.valueOf(evalt.recall(0)));
			row.add(String.valueOf(evalt.recall(1)));
			row.add(String.valueOf(evalt.fMeasure(0)));
			row.add(String.valueOf(evalt.fMeasure(1)));
			
			row.add(String.valueOf(b_eval.precision(0)));
			row.add(String.valueOf(b_eval.precision(1)));
			row.add(String.valueOf(b_eval.recall(0)));
			row.add(String.valueOf(b_eval.recall(1)));
			row.add(String.valueOf(b_eval.fMeasure(0)));
			row.add(String.valueOf(b_eval.fMeasure(1)));
			
			
			row.add(String.valueOf(entire_set.size()));

			results.add(row.toString());
			// row: [classifier, dataset, trainingset pct_correction, testset pct_correction, balancedset pct correction, crossvalid pct_correction, safe test precision, safe test recall, safe test fmeasure, safe testfmeasure, safe test precision, safe balance recall, safe balance fmeasure, safe balance fmeasure, setsize]
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
	}});
	return results;
	}
	
	static void writeResultTo(String output, List<String> content) throws IOException {
		Boolean append = true;
		FileWriter writer = new FileWriter(output, append);
		writer.write("\n");
		for(String s : content) {
            String[] split2 = s.split(",");
            writer.write(Arrays.asList(split2).stream().collect(Collectors.joining(",")));
            writer.write("\n"); // newline
        }

        writer.close();

	}
	static Instances loadData(String path) throws IOException{
		Instances data = null;

        try {
            data = DataSource.read(path);
            if (data.classIndex() == -1) {
                data.setClassIndex(data.numAttributes() - 1);
            }
        } catch (Exception e) {
			e.printStackTrace();

        }

        return data;
	}
	static double[] makePrediction(String modelPath, Instances inst) {
		double result = -1;
		Classifier cls = null;
		double results[] = new double[inst.size()];
		//System.out.println(inst.classAttribute());
        try {
            cls = (Classifier) weka.core.SerializationHelper
                    .read(modelPath);
        } catch (Exception e) {
            e.printStackTrace();
        }
        for(int i=0; i< inst.size(); i++ ) {
        	result = -1;
    	try {
    		result = cls.classifyInstance(inst.instance(i));
    		//System.out.println(result);
    	} catch (Exception e) {
    		e.printStackTrace();
    	  }
		}
		return results;
	}
	public static void main(String[] args) throws Exception {
	/*
		System.out.println(args[0]);
		System.out.println(args[1]);
		System.out.println(args[2]);
		System.out.println(args[3]);
		*/
		//String training_set = args[0];
		//String output = args[1];

		//String toTestPath = args[0];
		//String modelPath = args[1];
		
		WekaClassifier wekaClassifier = new WekaClassifier();
		//System.out.println("ClassifierToolChain: "+wekaClassifier.getClassifierToolChain());
		List<Classifier> classifiers =  wekaClassifier.getClassifiers();
		String modelPath = "C:/workspace/MasterThesis/datasets/test.model";
		String toTestPath = "C:/workspace/MasterThesis/datasets/test_prediction.csv";

		Instances toTest = WekaClassifier.loadData(toTestPath);
		//Instance inst = toTest.instance(0);
		double results [] = wekaClassifier.makePrediction(modelPath, toTest);
		for(int i=0; i<results.length; i++) {
			System.out.println("Index " + i + " Result "+ results[i]);
		}
	//	System.out.println("Result: " + result);
		//Instances training = WekaClassifier.loadData(training_set);
	//	List<String> outputPaths = wekaClassifier.saveClassifier(training, classifiers, output);
		//System.out.println(outputPaths);
		/*
		Instances test = WekaClassifier.loadData(args[1]);
		Instances balanced = WekaClassifier.loadData(args[2]);
		wekaClassifier.trainClassifier(training, classifiers);
		List<String> results = wekaClassifier.evaluateClassifier(training, test, balanced, classifiers, args[3]);
		System.out.println("result: "+results);
		wekaClassifier.writeResultTo(args[4], results);
		System.out.println("output: "+args[4]);
		*/
		/*
		Instances test = WekaClassifier.loadData("C:/workspace/MasterThesis/datasets/mixed_beam_driver/complete_beamng.csv");
		Instances training = WekaClassifier.loadData("C:/workspace/MasterThesis/datasets/mixed_beam_driver/complete_driver.csv");
		Instances balanced = WekaClassifier.loadData("C:/workspace/MasterThesis/datasets/mixed_beam_driver/complete_driver.csv");
		wekaClassifier.trainClassifier(training, classifiers);
		List<String> results = wekaClassifier.evaluateClassifier(training, test, balanced, classifiers, "mix_complete_driver_beam");
		String output= "C:/workspace/MasterThesis/datasets/result_v3.csv";
		System.out.println("result: "+results);
		wekaClassifier.writeResultTo(output, results);
		System.out.println("output: "+output);
		*/
		
	}
	
}
