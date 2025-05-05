import React from "react";
import { useVannaQuery } from "@/hooks/use-vanna-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Spinner } from "@/components/ui/spinner";
import { CodeBlock } from "@/components/ui/code-block";
import { DataTable } from "@/components/results/data-table";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export const VannaQuery: React.FC = () => {
  const {
    question,
    setQuestion,
    sqlResult,
    sqlLoading,
    dataResult,
    dataLoading,
    plotlyResult,
    plotlyLoading,
    followupResult,
    followupLoading,
    history,
    isHistoryLoading,
    handleQuery,
    loadQuestion
  } = useVannaQuery();

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleQuery();
    }
  };

  const handleFollowupClick = (followupQuestion: string) => {
    setQuestion(followupQuestion);
    handleQuery();
  };

  const handleHistoryClick = (id: string) => {
    loadQuestion(id);
  };

  return (
    <div className="space-y-4">
      <div className="flex space-x-2">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your data..."
          className="flex-1"
        />
        <Button onClick={handleQuery} disabled={sqlLoading || dataLoading}>
          {(sqlLoading || dataLoading) ? <Spinner size="sm" /> : "Ask"}
        </Button>
      </div>

      {sqlResult && (
        <Card>
          <CardHeader>
            <CardTitle>SQL Query</CardTitle>
          </CardHeader>
          <CardContent>
            <CodeBlock language="sql" code={sqlResult.text} />
          </CardContent>
        </Card>
      )}

      {dataResult && (
        <Tabs defaultValue="table">
          <TabsList>
            <TabsTrigger value="table">Table</TabsTrigger>
            {plotlyResult && <TabsTrigger value="chart">Chart</TabsTrigger>}
          </TabsList>
          <TabsContent value="table">
            <Card>
              <CardHeader>
                <CardTitle>Results</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable data={JSON.parse(dataResult.df)} />
              </CardContent>
            </Card>
          </TabsContent>
          {plotlyResult && (
            <TabsContent value="chart">
              <Card>
                <CardHeader>
                  <CardTitle>Visualization</CardTitle>
                </CardHeader>
                <CardContent>
                  {plotlyLoading ? (
                    <div className="flex justify-center p-4">
                      <Spinner size="lg" />
                    </div>
                  ) : (
                    <Plot
                      data={JSON.parse(plotlyResult.fig).data}
                      layout={JSON.parse(plotlyResult.fig).layout}
                      config={{ responsive: true }}
                      style={{ width: "100%", height: "400px" }}
                    />
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      )}

      {followupResult && (
        <Card>
          <CardHeader>
            <CardTitle>{followupResult.header}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {followupResult.questions.map((q, i) => (
                <Button
                  key={i}
                  variant="outline"
                  onClick={() => handleFollowupClick(q)}
                >
                  {q}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {history && history.questions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Questions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.questions.map((item) => (
                <Button
                  key={item.id}
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => handleHistoryClick(item.id)}
                >
                  {item.question}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
