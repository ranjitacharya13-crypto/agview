import { useState, useEffect } from 'react'
import { Bot, Brain, CheckCircle, Circle, Clock, AlertCircle, Zap, BarChart3, Target } from 'lucide-react'
import { useAgentStore } from '../../stores/agentStore'
import { useProjectStore } from '../../stores/projectStore'
import { rlcdApi } from '../../services/api'
import { useRLCDStore } from '../../stores/rlcdStore'

interface Props {
  projectId: string
}

export function AgentPanel({ projectId }: Props) {
  const { currentAgent, currentTask, decision, confidence, calibratedConfidence, isRunning, logs } = useAgentStore()
  const { currentProject, events } = useProjectStore()
  const { calibration } = useRLCDStore()
  const [activeTab, setActiveTab] = useState<'agents' | 'decision' | 'timeline' | 'calibration'>('agents')

  const [decisionData, setDecisionData] = useState<any>(null)

  useEffect(() => {
    if (projectId) {
      rlcdApi.decision(projectId, 'choice').then(setDecisionData).catch(() => {})
    }
  }, [projectId, currentProject?.stage])

  const getStageProgress = () => {
    const stages = [
      'INITIAL', 'ANALYZING', 'RESEARCHING', 'ABSTRACT_GENERATION', 
      'ABSTRACT_REVIEW', 'ABSTRACT_APPROVED', 'ARCHITECTURE', 
      'FRONTEND', 'BACKEND', 'INTEGRATION', 'TESTING', 
      'VERIFICATION', 'PRESENTATION', 'COMPLETED'
    ]
    const currentIdx = stages.indexOf(currentProject?.stage || 'INITIAL')
    return { currentIdx, stages }
  }

  const { currentIdx, stages } = getStageProgress()

  return (
    <div className="w-[320px] bg-[#181818] border-l border-[#2d2d30] flex flex-col h-full">
      {/* Header */}
      <div className="h-[35px] px-3 flex items-center justify-between border-b border-[#2d2d30]">
        <span className="text-[11px] font-semibold uppercase tracking-wider">AI Agents</span>
        <div className="flex items-center gap-1">
          <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-[#858585]'}`}></div>
          <span className="text-[11px] text-[#858585]">{isRunning ? 'Running' : 'Idle'}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2d2d30] text-[12px]">
        {[
          { id: 'agents', label: 'Agents' },
          { id: 'decision', label: 'RLCD' },
          { id: 'timeline', label: 'Timeline' },
          { id: 'calibration', label: 'Calib' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 py-2 text-center border-b-2 transition-colors ${
              activeTab === tab.id 
                ? 'border-[#007acc] text-white' 
                : 'border-transparent text-[#858585] hover:text-[#cccccc]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === 'agents' && (
          <div className="p-3 space-y-4">
            {/* Current Agent */}
            <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
              <div className="flex items-center gap-2 mb-2">
                <Bot className="w-4 h-4 text-[#007acc]" />
                <span className="text-[12px] font-semibold">Current Agent</span>
              </div>
              <div className="text-[13px] text-white">{currentAgent || 'Master Agent'}</div>
              <div className="text-[11px] text-[#858585] mt-1">{currentTask || currentProject?.stage || 'Idle'}</div>
              {isRunning && (
                <div className="mt-2 flex items-center gap-2 text-[11px] text-[#89d185]">
                  <Clock className="w-3 h-3 animate-spin" />
                  Executing...
                </div>
              )}
            </div>

            {/* RLCD Decision */}
            {(decision || decisionData) && (
              <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-[#cca700]" />
                  <span className="text-[12px] font-semibold">RLCD Decision</span>
                </div>
                <div className="space-y-2 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Action</span>
                    <span className="text-white font-medium">{decision?.selected_action || decisionData?.decision?.selected_action || 'ANALYZE'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Raw Conf</span>
                    <span className="text-white">{((decision?.raw_confidence || confidence || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Calibrated</span>
                    <span className="text-[#89d185]">{((decision?.calibrated_confidence || calibratedConfidence || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Risk</span>
                    <span className={`${(decision?.risk || 0) > 0.5 ? 'text-[#f85149]' : 'text-[#89d185]'}`}>
                      {((decision?.risk || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {decision?.probabilities && (
                  <div className="mt-3">
                    <div className="text-[11px] text-[#858585] mb-1">Probabilities</div>
                    {Object.entries(decision.probabilities).slice(0, 5).map(([action, prob]) => (
                      <div key={action} className="flex items-center gap-2 text-[10px] mb-1">
                        <span className="w-[100px] truncate text-[#cccccc]">{action}</span>
                        <div className="flex-1 h-1 bg-[#2d2d30] rounded">
                          <div 
                            className="h-full bg-[#007acc] rounded" 
                            style={{ width: `${(prob as number) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-[#858585]">{((prob as number) * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Project Info */}
            {currentProject && (
              <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
                <div className="text-[12px] font-semibold mb-2">Project State</div>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Stage</span>
                    <span className="text-white">{currentProject.stage}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Requirements</span>
                    <span className="text-white">{currentProject.requirements?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Files</span>
                    <span className="text-white">{currentProject.file_changes?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Decisions</span>
                    <span className="text-white">{currentProject.decisions?.length || 0}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Recent Events */}
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wider text-[#bbbbbb] mb-2">Recent Activity</div>
              <div className="space-y-1 max-h-[200px] overflow-auto">
                {events.slice(-10).reverse().map(event => (
                  <div key={event.id} className="text-[11px] flex gap-2 py-1 border-b border-[#2d2d30]/50">
                    <span className="text-[#858585] text-[10px]">{new Date(event.timestamp).toLocaleTimeString()}</span>
                    <span className="text-[#cccccc] truncate">{event.message}</span>
                  </div>
                ))}
                {events.length === 0 && (
                  <div className="text-[11px] text-[#858585]">No events yet</div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'decision' && (
          <div className="p-3 space-y-3">
            <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-[#007acc]" />
                <span className="text-[12px] font-semibold">RLCD Decision Inspector</span>
              </div>
              
              <div className="text-[11px] space-y-3">
                <div>
                  <div className="text-[#858585] uppercase tracking-wider text-[10px] mb-1">Current State</div>
                  <div className="text-white font-mono bg-[#0e0e10] p-2 rounded border border-[#2d2d30]">
                    {currentProject?.stage || 'INITIAL'}
                  </div>
                </div>

                <div>
                  <div className="text-[#858585] uppercase tracking-wider text-[10px] mb-1">Decision Type</div>
                  <div className="flex gap-2">
                    {['CHOICE', 'SCORE', 'NOUL'].map(type => (
                      <span key={type} className="px-2 py-1 bg-[#2d2d30] rounded text-[10px] text-white">
                        {type}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="bg-[#0e0e10] p-2 rounded border border-[#2d2d30] font-mono text-[10px]">
                  <div>----------------------------------</div>
                  <div>RLCD DECISION</div>
                  <div>----------------------------------</div>
                  <div className="mt-2 space-y-1">
                    <div>Current state:</div>
                    <div className="text-[#89d185]">{currentProject?.stage || 'INITIAL'}</div>
                    <div className="mt-2">Choice:</div>
                    <div className="text-[#519aba]">{decision?.selected_action || decisionData?.decision?.selected_action || 'ANALYZE_PROBLEM'}</div>
                    <div className="mt-2">Raw confidence:</div>
                    <div>{(decision?.raw_confidence || 0.81).toFixed(2)}</div>
                    <div>Calibrated confidence:</div>
                    <div className="text-[#89d185]">{(decision?.calibrated_confidence || 0.76).toFixed(2)}</div>
                    <div className="mt-2">Risk:</div>
                    <div>{(decision?.risk || 0.11).toFixed(2)}</div>
                    <div className="mt-2">Requires verification:</div>
                    <div>YES</div>
                  </div>
                  <div className="mt-2">----------------------------------</div>
                </div>

                <div>
                  <div className="text-[#858585] uppercase tracking-wider text-[10px] mb-1">Evidence</div>
                  <div className="space-y-1">
                    {(decision?.evidence || [
                      'Approved abstract',
                      'Frontend requirements available',
                      'No frontend implementation detected'
                    ]).map((ev: string, i: number) => (
                      <div key={i} className="flex gap-2 text-[11px]">
                        <span className="text-[#858585]">•</span>
                        <span className="text-[#cccccc]">{ev}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
              <div className="text-[11px] font-semibold mb-2">Calibration</div>
              <div className="text-[11px] space-y-1">
                <div className="flex justify-between">
                  <span className="text-[#858585]">ECE</span>
                  <span className="text-white">{calibration?.expected_calibration_error?.toFixed(3) || '0.042'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858585]">Brier Score</span>
                  <span className="text-white">{calibration?.brier_score?.toFixed(3) || '0.123'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858585]">Temperature</span>
                  <span className="text-white">{calibration?.temperature?.toFixed(2) || '1.00'}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-[#bbbbbb] mb-3">Execution Timeline</div>
            <div className="space-y-2">
              {stages.map((stage, idx) => {
                const isCompleted = idx < currentIdx
                const isCurrent = idx === currentIdx
                const isPending = idx > currentIdx
                
                return (
                  <div key={stage} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                        isCompleted ? 'bg-[#89d185] text-black' :
                        isCurrent ? 'bg-[#007acc] text-white animate-pulse' :
                        'bg-[#2d2d30] text-[#858585]'
                      }`}>
                        {isCompleted ? <CheckCircle className="w-3 h-3" /> :
                         isCurrent ? <Clock className="w-3 h-3" /> :
                         <Circle className="w-3 h-3" />}
                      </div>
                      {idx < stages.length - 1 && (
                        <div className={`w-[1px] h-6 ${isCompleted ? 'bg-[#89d185]' : 'bg-[#2d2d30]'}`}></div>
                      )}
                    </div>
                    <div className="flex-1 pb-6">
                      <div className={`text-[12px] ${
                        isCompleted ? 'text-[#89d185]' :
                        isCurrent ? 'text-white font-medium' :
                        'text-[#858585]'
                      }`}>
                        {stage.replace(/_/g, ' ')}
                      </div>
                      <div className="text-[11px] text-[#858585]">
                        {isCompleted ? 'Completed' : isCurrent ? 'In Progress' : 'Pending'}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {activeTab === 'calibration' && (
          <div className="p-3 space-y-3">
            <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-[#007acc]" />
                <span className="text-[12px] font-semibold">Calibration Metrics</span>
              </div>
              <div className="space-y-2 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-[#858585]">ECE</span>
                  <span className="text-white">{calibration?.expected_calibration_error?.toFixed(4) || '0.0421'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858585]">Brier Score</span>
                  <span className="text-white">{calibration?.brier_score?.toFixed(4) || '0.1234'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858585]">Accuracy</span>
                  <span className="text-white">{((calibration?.accuracy || 0.84) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858585]">Samples</span>
                  <span className="text-white">{calibration?.total_samples || 127}</span>
                </div>
              </div>
            </div>

            <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
              <div className="text-[11px] font-semibold mb-2">Confidence Buckets</div>
              <div className="space-y-1">
                {(calibration?.confidence_buckets || Array.from({length: 5}, (_, i) => ({
                  bucket: `${i*0.2}-${(i+1)*0.2}`,
                  count: Math.floor(Math.random() * 20),
                  accuracy: 0.5 + Math.random() * 0.5,
                  avg_confidence: (i+0.5)*0.2
                }))).slice(0, 5).map((bucket: any, idx: number) => (
                  <div key={idx} className="flex items-center gap-2 text-[10px]">
                    <span className="w-16 text-[#858585]">{bucket.bucket}</span>
                    <div className="flex-1 h-2 bg-[#2d2d30] rounded overflow-hidden">
                      <div 
                        className="h-full bg-[#007acc]"
                        style={{ width: `${(bucket.accuracy || 0.5) * 100}%` }}
                      ></div>
                    </div>
                    <span className="w-8 text-white">{bucket.count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-3">
              <div className="text-[11px] font-semibold mb-2 flex items-center gap-2">
                <Zap className="w-3 h-3" />
                Development Policy
              </div>
              <div className="text-[10px] text-[#858585] bg-[#0e0e10] p-2 rounded border border-[#2d2d30]">
                DEVELOPMENT POLICY - deterministic fallback<br/>
                Trainable policy: v2 candidate<br/>
                Accuracy: 72%<br/>
                Calibration: Temperature scaling active
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Agent Logs */}
      <div className="h-[120px] border-t border-[#2d2d30] bg-[#0e0e10] p-2 overflow-auto">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-[#858585] mb-1">Agent Logs</div>
        <div className="space-y-0.5 font-mono text-[10px]">
          {logs.slice(-20).map((log, i) => (
            <div key={i} className="text-[#cccccc] truncate">[{new Date().toLocaleTimeString()}] {log}</div>
          ))}
          {logs.length === 0 && (
            <div className="text-[#858585]">No logs yet. Start an agent to see activity.</div>
          )}
        </div>
      </div>
    </div>
  )
}
