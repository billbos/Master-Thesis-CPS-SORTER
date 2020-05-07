package org.zhaw.ch.ml;

public abstract class  MachineLearningClassifier {

	protected String classifierToolChain;
	
	protected String machineLearningModelName;

	public String getClassifierToolChain() {
		return classifierToolChain;
	}

	public void setClassifierToolChain(String classifierToolChain) {
		this.classifierToolChain = classifierToolChain;
	}

	public String getMachineLearningModelName() {
		return machineLearningModelName;
	}

	public void setMachineLearningModelName(String machineLearningModelName) {
		this.machineLearningModelName = machineLearningModelName;
	}
	
	
}
