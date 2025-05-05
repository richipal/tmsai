import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  generateSql, 
  runSql, 
  generatePlotlyFigure, 
  generateFollowupQuestions,
  getQuestionHistory,
  loadQuestion
} from "@/lib/flask-service";

export const useVannaQuery = () => {
  const [question, setQuestion] = useState<string>("");
  const [currentId, setCurrentId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  
  const generateSqlMutation = useMutation({
    mutationFn: generateSql,
    onSuccess: (data) => {
      setCurrentId(data.id);
    }
  });
  
  const runSqlMutation = useMutation({
    mutationFn: runSql,
    onSuccess: () => {
      if (currentId) {
        generatePlotlyMutation.mutate(currentId);
        generateFollowupMutation.mutate(currentId);
      }
    }
  });
  
  const generatePlotlyMutation = useMutation({
    mutationFn: generatePlotlyFigure
  });
  
  const generateFollowupMutation = useMutation({
    mutationFn: generateFollowupQuestions
  });
  
  const { data: history, isLoading: isHistoryLoading } = useQuery({
    queryKey: ['question_history'],
    queryFn: getQuestionHistory,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  const loadQuestionMutation = useMutation({
    mutationFn: loadQuestion,
    onSuccess: (data) => {
      setCurrentId(data.id);
      setQuestion(data.question);
    }
  });
  
  const handleQuery = async () => {
    if (!question.trim()) return;
    
    try {
      const sqlResult = await generateSqlMutation.mutateAsync(question);
      
      await runSqlMutation.mutateAsync(sqlResult.id);
      
      queryClient.invalidateQueries({ queryKey: ['question_history'] });
    } catch (error) {
      console.error("Error in query flow:", error);
    }
  };
  
  return {
    question,
    setQuestion,
    currentId,
    
    generateSql: generateSqlMutation.mutate,
    runSql: runSqlMutation.mutate,
    generatePlotly: generatePlotlyMutation.mutate,
    generateFollowup: generateFollowupMutation.mutate,
    loadQuestion: loadQuestionMutation.mutate,
    
    sqlResult: generateSqlMutation.data,
    sqlLoading: generateSqlMutation.isPending,
    sqlError: generateSqlMutation.error,
    
    dataResult: runSqlMutation.data,
    dataLoading: runSqlMutation.isPending,
    dataError: runSqlMutation.error,
    
    plotlyResult: generatePlotlyMutation.data,
    plotlyLoading: generatePlotlyMutation.isPending,
    plotlyError: generatePlotlyMutation.error,
    
    followupResult: generateFollowupMutation.data,
    followupLoading: generateFollowupMutation.isPending,
    followupError: generateFollowupMutation.error,
    
    loadedQuestion: loadQuestionMutation.data,
    loadingQuestion: loadQuestionMutation.isPending,
    loadError: loadQuestionMutation.error,
    
    history,
    isHistoryLoading,
    
    handleQuery
  };
};
