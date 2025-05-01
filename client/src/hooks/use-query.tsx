import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { executeQuery, getQueryHistory, getSavedQueries, saveQuery, unsaveQuery, QueryResultData, QueryHistoryItem } from "@/lib/flask-service";

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
