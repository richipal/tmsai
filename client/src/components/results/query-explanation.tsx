import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface QueryExplanationProps {
  explanation: string;
}

export default function QueryExplanation({ explanation }: QueryExplanationProps) {
  if (!explanation) {
    return null;
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg leading-6 font-medium text-gray-900">
          Query Explanation
        </CardTitle>
        <CardDescription className="mt-1 text-sm text-gray-500">
          Understanding what your query does
        </CardDescription>
      </CardHeader>
      <CardContent className="border-t border-gray-200 px-4 py-5 sm:p-6">
        <div className="prose prose-sm max-w-none text-gray-500">
          {explanation.split('\n').map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
