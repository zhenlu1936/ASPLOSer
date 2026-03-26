# Holistic Model Picture

This diagram is auto-generated from the current scenario graph.

Generated image: scenario3_pic.svg

```mermaid
flowchart LR
  %% Auto-generated holistic model view
  subgraph Agent[Agents]
    n_InferenceModule["InferenceModule\ncredibility: Trusted\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_IntelligentSystem["IntelligentSystem\ncredibility: MixedCredibility\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_PostprocessingModule["PostprocessingModule\ncredibility: Trusted\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_PreprocessingModule["PreprocessingModule\ncredibility: Trusted\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
  end
  subgraph Participant[Participants]
    n_AppDeveloper["AppDeveloper\ncredibility: Untrusted\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_DataWorker["DataWorker\ncredibility: Untrusted\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_Maintainer["Maintainer\ncredibility: Untrusted\ncorrectness: MixedCorrectness\ncontinuity: Discontinuous"]
    n_ModelDeveloper["ModelDeveloper\ncredibility: Trusted\ncorrectness: Correct\ncontinuity: Continuous"]
    n_OperatingEnvironment["OperatingEnvironment\ncredibility: MixedCredibility\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_User["User\ncredibility: Trusted\ncorrectness: Correct\ncontinuity: Continuous"]
  end
  subgraph Source[Sources]
    n_AppHub["AppHub\nconfidentiality: NonConfidential\ncorrectness: MixedCorrectness\ncontinuity: Continuous"]
    n_DependencyHub["DependencyHub\nconfidentiality: NonConfidential\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_ModelHub["ModelHub\nconfidentiality: NonConfidential\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
  end
  subgraph Asset[Assets]
    n_Application["Application\nconfidentiality: NonConfidential\ncorrectness: MixedCorrectness\ncontinuity: Continuous"]
    n_ApplicationProgrammed["ApplicationProgrammed\nconfidentiality: NonConfidential\ncorrectness: MixedCorrectness\ncontinuity: Continuous"]
    n_Dependency["Dependency\nconfidentiality: NonConfidential\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_InputQuery["InputQuery\nconfidentiality: Confidential\ncorrectness: Correct\ncontinuity: Continuous"]
    n_InputToken["InputToken\nconfidentiality: Confidential\ncorrectness: Correct\ncontinuity: Continuous"]
    n_Model["Model\nconfidentiality: Confidential\ncorrectness: Correct\ncontinuity: Continuous"]
    n_ModelPretrained["ModelPretrained\nconfidentiality: NonConfidential\ncorrectness: MixedCorrectness\ncontinuity: MixedContinuity"]
    n_ModelTrained["ModelTrained\nconfidentiality: Confidential\ncorrectness: Correct\ncontinuity: Continuous"]
    n_OutputMaterialized["OutputMaterialized\nconfidentiality: MixedConfidentiality\ncorrectness: Correct\ncontinuity: Continuous"]
    n_OutputToken["OutputToken\nconfidentiality: MixedConfidentiality\ncorrectness: Correct\ncontinuity: Continuous"]
    n_ProcessedData["ProcessedData\nconfidentiality: Confidential\ncorrectness: MixedCorrectness\ncontinuity: Continuous"]
    n_RawData["RawData\nconfidentiality: Confidential\ncorrectness: Correct\ncontinuity: Continuous"]
  end
  n_RawData -.->|1.Process (ActedOnBy)| n_DataWorker
  n_DataWorker -->|1.Process (Act)| n_ProcessedData
  n_ProcessedData -.->|2.Train (ActedOnBy)| n_ModelDeveloper
  n_ModelPretrained -.->|2.Train (ActedOnBy)| n_ModelDeveloper
  n_ModelDeveloper -->|2.Train (Act)| n_ModelTrained
  n_ModelTrained -.->|3.Upload (ActedOnBy)| n_ModelDeveloper
  n_ModelDeveloper -->|3.Upload (Act)| n_ModelHub
  n_ModelHub -.->|4.Download (ActedOnBy)| n_Maintainer
  n_Maintainer -->|4.Download (Act)| n_Model
  n_AppDeveloper -->|5.Program (Act)| n_ApplicationProgrammed
  n_ApplicationProgrammed -.->|6.Upload (ActedOnBy)| n_AppDeveloper
  n_AppDeveloper -->|6.Upload (Act)| n_AppHub
  n_AppHub -.->|7.Download (ActedOnBy)| n_Maintainer
  n_Maintainer -->|7.Download (Act)| n_Application
  n_DependencyHub -.->|8.Download (ActedOnBy)| n_Maintainer
  n_Maintainer -->|8.Download (Act)| n_Dependency
  n_Model -.->|9.Assemble (ActedOnBy)| n_Maintainer
  n_Application -.->|9.Assemble (ActedOnBy)| n_Maintainer
  n_Dependency -.->|9.Assemble (ActedOnBy)| n_Maintainer
  n_Maintainer -->|9.Assemble (Act)| n_IntelligentSystem
  n_User -->|10.Propose (Act)| n_InputQuery
  n_InputQuery -.->|11.Pre-Process (ActedOnBy)| n_PreprocessingModule
  n_PreprocessingModule -->|11.Pre-Process (Act)| n_InputToken
  n_InputToken -.->|12.Inference (ActedOnBy)| n_InferenceModule
  n_InferenceModule -->|12.Inference (Act)| n_OutputToken
  n_OutputToken -.->|13.Post-Process (ActedOnBy)| n_PostprocessingModule
  n_PostprocessingModule -->|13.Post-Process (Act)| n_OutputMaterialized
  n_PreprocessingModule --|ComponentOf (ComponentOf)| n_IntelligentSystem
  n_InferenceModule --|ComponentOf (ComponentOf)| n_IntelligentSystem
  n_PostprocessingModule --|ComponentOf (ComponentOf)| n_IntelligentSystem
  n_IntelligentSystem --|ComponentOf (ComponentOf)| n_OperatingEnvironment
  n_OutputMaterialized ==>|R1.Respond (Respond)| n_User
  n_OutputMaterialized ==>|R2.Respond (Respond)| n_OperatingEnvironment
  n_OperatingEnvironment ==>|R3.Respond (Respond)| n_IntelligentSystem
  n_User ==>|R4.Respond (Respond)| n_DataWorker
  n_User ==>|R5.Respond (Respond)| n_ModelDeveloper
  n_User ==>|R6.Respond (Respond)| n_AppDeveloper
  n_User ==>|R7.Respond (Respond)| n_Maintainer
```
