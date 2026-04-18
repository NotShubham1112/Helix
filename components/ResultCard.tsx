"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle2, Clock } from "lucide-react";

interface Risk {
  condition: string;
  probability: string;
  reason: string;
}

interface Recommendation {
  action: string;
  urgency: string;
}

interface ResultCardProps {
  data: {
    summary: string;
    abnormalities: string[];
    risks: Risk[];
    recommendations: Recommendation[];
    confidence: number;
    timestamp?: string;
  };
}

export default function ResultCard({ data }: ResultCardProps) {
  if (!data) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-muted-foreground">No results to display</p>
        </CardContent>
      </Card>
    );
  }

  const getUrgencyColor = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getProbabilityColor = (probability: string) => {
    const lower = probability.toLowerCase();
    if (lower.includes("high")) return "bg-red-50";
    if (lower.includes("medium")) return "bg-yellow-50";
    if (lower.includes("low")) return "bg-green-50";
    return "bg-gray-50";
  };

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Clinical Summary</CardTitle>
            <Badge variant="outline" className="text-xs">
              {(data.confidence * 100).toFixed(0)}% confidence
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{data.summary}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Abnormalities */}
      {data.abnormalities && data.abnormalities.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Abnormal Values</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.abnormalities.map((abnormality, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 p-2 rounded bg-orange-50 border border-orange-200"
                >
                  <AlertCircle className="h-4 w-4 text-orange-600 flex-shrink-0" />
                  <span className="text-sm">{abnormality}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Risk Assessment */}
      {data.risks && data.risks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Risk Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.risks.map((risk, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border ${getProbabilityColor(
                    risk.probability
                  )}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{risk.condition}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {risk.reason}
                      </p>
                    </div>
                    <Badge variant="secondary" className="text-xs whitespace-nowrap">
                      {risk.probability}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recommended Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.recommendations.map((rec, idx) => (
                <div key={idx} className="flex gap-3">
                  <div className="flex-shrink-0 mt-1">
                    {rec.urgency === "High" ? (
                      <AlertCircle className="h-5 w-5 text-red-600" />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    )}
                  </div>

                  <div className="flex-1">
                    <p className="text-sm font-medium">{rec.action}</p>
                    <Badge
                      className={`text-xs mt-1 ${getUrgencyColor(rec.urgency)}`}
                      variant="outline"
                    >
                      {rec.urgency} Priority
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      <Alert className="bg-blue-50 border-blue-200">
        <AlertCircle className="h-4 w-4 text-blue-600" />
        <AlertDescription className="text-xs text-blue-800">
          This analysis is for informational purposes only. Always consult with a
          qualified healthcare provider before making any medical decisions.
        </AlertDescription>
      </Alert>

      {/* Timestamp */}
      {data.timestamp && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{new Date(data.timestamp).toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}
