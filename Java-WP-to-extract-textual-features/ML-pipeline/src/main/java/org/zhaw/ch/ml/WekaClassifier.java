package org.zhaw.ch.ml;
import weka.core.Instances;
import weka.core.converters.CSVLoader;
import weka.core.converters.ConverterUtils.DataSource;
import weka.classifiers.trees.J48;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map.Entry;
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
	static List<Classifier> getClassifiers(){
		List<Classifier> classifiers = new ArrayList<Classifier>();
		Classifier j48 = new J48();
		Classifier naiveBayes = new NaiveBayes();
		Classifier logistic = new Logistic();
		classifiers.addAll(Arrays.asList(j48, naiveBayes, logistic));
		return classifiers;
	}
	static void trainClassifier(Instances training, List<Classifier> classifiers){
		classifiers.stream().forEach(cls -> {try {
			cls.buildClassifier(training);
		} catch (Exception e) {
			e.printStackTrace();
		}});
	}
	
	static List<String> evaluateClassifier(Instances training, Instances test, List<Classifier> classifiers, String filename) throws Exception{
	System.out.println("Starting....");
	List<String> results = new ArrayList<String>(); 
	// evaluate classifier and print some statistics
	classifiers.stream().forEach(cls -> {
		try {
			StringJoiner row = new StringJoiner(","); 
			row.add(cls.getClass().toString());
			row.add(filename);
			Evaluation eval = new Evaluation(training);
			eval.evaluateModel(cls, training);
			row.add(String.valueOf(eval.pctCorrect()));
			Evaluation evalt = new Evaluation(training);
			evalt.evaluateModel(cls, test);
			row.add(String.valueOf(evalt.pctCorrect()));
			row.add(String.valueOf(evalt.precision(0)));
			row.add(String.valueOf(evalt.precision(1)));
			row.add(String.valueOf(evalt.recall(0)));
			row.add(String.valueOf(evalt.recall(1)));
			results.add(row.toString());

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
	
	public static void main(String[] args) throws Exception {
		System.out.println(args[0]);
		System.out.println(args[1]);
		System.out.println(args[2]);

		WekaClassifier wekaClassifier = new WekaClassifier();
		System.out.println("ClassifierToolChain: "+wekaClassifier.getClassifierToolChain());
		List<Classifier> classifiers =  wekaClassifier.getClassifiers();
		Instances training = WekaClassifier.loadData(args[0]);
		Instances test = WekaClassifier.loadData(args[1]);
		wekaClassifier.trainClassifier(training, classifiers);
		List<String> results = wekaClassifier.evaluateClassifier(training, test, classifiers, args[2]);
		System.out.println("result: "+results);
		wekaClassifier.writeResultTo(args[3], results);
		System.out.println("output: "+args[3]);

	}
	
}
