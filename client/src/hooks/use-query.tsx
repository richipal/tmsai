import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  executeQuery, 
  getQueryHistory, 
  getSavedQueries, 
  saveQuery, 
  unsaveQuery, 
  getExampleQuestions,
  getTrainingData,
  trainModel,
  QueryResultData, 
  QueryHistoryItem,
  ExampleQuestionsData,
  TrainingData
} from "@/lib/flask-service";

export const useNaturalLanguageQuery = (databaseConnectionId: number) => {
  const [queryInput, setQueryInput] = useState<string>("");
  const queryClient = useQueryClient();
  
  const {
    mutate,
    data: queryResult,
    isPending,
    isError,
    error
  } = useMutation({
    mutationFn: (nlQuery: string) => executeQuery(nlQuery, databaseConnectionId),
    onSuccess: () => {
      // Invalidate query history after a successful query
      queryClient.invalidateQueries({ queryKey: ['/api/history'] });
    }
  });
  
  const handleExecuteQuery = () => {
    if (queryInput.trim()) {
      mutate(queryInput);
    }
  };
  
  // No longer need this as it's handled directly in dashboard component
  
  return {
    queryInput,
    setQueryInput,
    queryResult,
    isPending,
    isError,
    error,
    handleExecuteQuery
  };
};

export const useQueryHistory = () => {
  const { data: history, isLoading, error } = useQuery({
    queryKey: ['/api/history'],
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  return {
    history: history as QueryHistoryItem[] | undefined,
    isLoading,
    error
  };
};

export const useSavedQueries = () => {
  const { data: savedQueries, isLoading, error } = useQuery({
    queryKey: ['/api/saved-queries'],
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  return {
    savedQueries: savedQueries as QueryHistoryItem[] | undefined,
    isLoading,
    error
  };
};

export const useQueryActions = () => {
  const queryClient = useQueryClient();
  
  const saveQueryMutation = useMutation({
    mutationFn: saveQuery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/history'] });
      queryClient.invalidateQueries({ queryKey: ['/api/saved-queries'] });
    }
  });
  
  const unsaveQueryMutation = useMutation({
    mutationFn: unsaveQuery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/history'] });
      queryClient.invalidateQueries({ queryKey: ['/api/saved-queries'] });
    }
  });
  
  return {
    saveQuery: saveQueryMutation.mutate,
    unsaveQuery: unsaveQueryMutation.mutate,
    isSaving: saveQueryMutation.isPending,
    isUnsaving: unsaveQueryMutation.isPending
  };
};

export const useExampleQuestions = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['/api/examples'],
    queryFn: getExampleQuestions,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  return {
    examples: data?.examples || [],
    isLoading,
    error
  };
};

export const useTrainingData = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['/api/training-data'],
    queryFn: getTrainingData,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  return {
    trainingData: data,
    isLoading,
    error
  };
};

export const useTrainModel = () => {
  const queryClient = useQueryClient();
  
  const trainModelMutation = useMutation({
    mutationFn: trainModel,
    onSuccess: () => {
      // Invalidate training data query to refresh
      queryClient.invalidateQueries({ queryKey: ['/api/training-data'] });
    }
  });
  
  return {
    trainModel: trainModelMutation.mutate,
    isTraining: trainModelMutation.isPending,
    error: trainModelMutation.error
  };
};
