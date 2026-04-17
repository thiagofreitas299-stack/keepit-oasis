import { useState } from "react";

const COLORS = {
  gold: "#C9A84C", green: "#00CC6A", navy: "#0B0B2B",
  midNavy: "#1A1A4A", accent: "#E8D5A3", red: "#FF4560",
  blue: "#008FFB", purple: "#775DD0", teal: "#00E396",
  orange: "#FEB019", white: "#F4F1E8", gray: "#6B7280",
};

function simulateDVCA() {
  const rand = (min, max) => Math.random() * (max - min) + min;
  const syncValidators = [
    { id: "V1_LogicConsistency", mode: "sync", score: rand(0.87, 0.99) },
    { id: "V2_EmpiricalEvidence", mode: "sync", score: rand(0.85, 0.98) },
    { id: "V3_CausalChain", mode: "sync", score: rand(0.86, 0.97) },
    { id: "V4_PriorBelief", mode: "sync", score: rand(0.88, 0.99) },
    { id: "V5_BiasDetector", mode: "sync", score: rand(0.85, 0.97) },
  ];
  const asyncValidators = [
    { id: "V6_CrossDomain", mode: "async", score: rand(0.84, 0.98) },
    { id: "V7_QuantRobustness", mode: "async", score: rand(0.87, 0.99) },
    { id: "V8_TemporalStability", mode: "async", score: rand(0.85, 0.97) },
    { id: "V9_Ethics", mode: "async", score: rand(0.90, 0.99) },
    { id: "V10_InfoEntropy", mode: "async", score: rand(0.86, 0.98) },
  ];
  const cvSync = [
    { id: "CV1_Falsification", mode: "sync", score: rand(0.86, 0.99) },
    { id: "CV2_AssumptionChallenge", mode: "sync", score: rand(0.87, 0.98) },
    { id: "CV3_ConfirmationBias", mode: "sync", score: rand(0.85, 0.97) },
  ];
  const cvAsync = [
    { id: "CV4_MonteCarloStress", mode: "async", score: rand(0.88, 0.99) },
    { id: "CV5_AltHypothesis", mode: "async", score: rand(0.85, 0.98) },
    { id: "CV6_AdversarialPerturbation", mode: "async", score: rand(0.86, 0.97) },
    { id: "CV7_InternalContradiction", mode: "async", score: rand(0.89, 0.99) },
  ];
  const vSync = syncValidators.reduce((s,v)=>s+v.score,0)/syncValidators.length;
  const vAsync = asyncValidators.reduce((s,v)=>s+v.score,0)/asyncValidators.length;
  const vFused = 0.55*vSync + 0.45*vAsync;
  const cvSyncS = cvSync.reduce((s,v)=>s+v.score,0)/cvSync.length;
  const cvAsyncS = cvAsync.reduce((s,v)=>s+v.score,0)/cvAsync.length;
  const cvFused = 0.5*cvSyncS + 0.5*cvAsyncS;
  const worldScore = rand(0.94, 0.999);
  const composite = 0.40*vFused + 0.35*cvFused + 0.25*worldScore;
  const riskAdj = composite * (1 - rand(0.005, 0.02));
  const winner = vFused >= cvFused ? "VALIDATION" : "COUNTER-VALIDATION";
  const winScore = Math.max(vFused, cvFused);
  const decision = composite >= 0.97 ? "APPROVE" : composite >= 0.93 ? "ESCALATE" : "REVISE";
  const vuln = [...cvSync,...cvAsync].reduce((acc,v)=>{acc[v.id]=parseFloat((1-v.score).toFixed(4));return acc;},{});
  const calReports = [...syncValidators,...asyncValidators].map(v=>({
    id:v.id, eceBefore:rand(0.15,0.40), eceAfter:rand(0.01,0.20)
  }));
  return {
    vSync,vAsync,vFused,cvSync:cvSyncS,cvAsync:cvAsyncS,cvFused,
    worldScore,composite,riskAdj,winner,winScore,decision,
    passed:vFused>=0.97&&cvFused>=0.97,
    syncValidators,asyncValidators,cvSync,cvAsync,vuln,calReports,
    reasoning:[
      `[1/6] VALIDATION SCORE: ${vFused.toFixed(4)} — ${vFused>=0.97?"✓ PASSOU":"⚠ ABAIXO DO LIMIAR"}`,
      `[2/6] COUNTER-VALIDATION SCORE: ${cvFused.toFixed(4)} — ${cvFused>=0.97?"✓ ROBUSTO":"⚠ VULNERÁVEL"}`,
      `[3/6] WINNER: ${winner} com score ${winScore.toFixed(4)}`,
      `[4/6] WORLD MODEL: mean=${worldScore.toFixed(3)} | tail_risk=${rand(0,0.05).toFixed(3)}`,
      `[5/6] COMPOSITE (V×0.40 + CV×0.35 + W×0.25): ${composite.toFixed(4)}`,
      `[6/6] MCTS DECISION: '${decision}' após exploração da árvore de decisão`,
    ],
  };
}

function ScoreBar({score,label,color,animate}){
  const pct=Math.round(score*100);
  return(
    <div style={{marginBottom:12}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
        <span style={{color:COLORS.accent,fontSize:11,fontFamily:"monospace"}}>{label}</span>
        <span style={{color:score>=0.97?COLORS.green:score>=0.93?COLORS.orange:COLORS.red,fontSize:12,fontWeight:"bold",fontFamily:"monospace"}}>{pct}%</span>
      </div>
      <div style={{height:8,background:"#1A1A4A",borderRadius:4,position:"relative"}}>
        <div style={{height:"100%",borderRadius:4,background:color,width:animate?`${pct}%`:"0%",transition:"width 1.2s ease",boxShadow:score>=0.97?`0 0 8px ${color}`:"none"}}/>
        <div style={{position:"absolute",top:-2,left:"97%",width:2,height:12,background:COLORS.gold,opacity:0.8}}/>
      </div>
    </div>
  );
}

function ValidatorCard({validator,index,animate}){
  const isAsync=validator.mode==="async";
  const passed=validator.score>=0.97;
  return(
    <div style={{background:COLORS.midNavy,border:`1px solid ${passed?COLORS.green:COLORS.orange}33`,borderRadius:8,padding:"10px 12px",marginBottom:8,opacity:animate?1:0,transition:`opacity 0.4s ${index*0.08}s`}}>
      <div style={{display:"flex",alignItems:"center",gap:8}}>
        <span style={{fontSize:9,fontFamily:"monospace",padding:"2px 6px",borderRadius:4,background:isAsync?"#1A2040":"#001A20",color:isAsync?COLORS.blue:COLORS.teal,border:`1px solid ${isAsync?COLORS.blue:COLORS.teal}44`}}>{validator.mode.toUpperCase()}</span>
        <span style={{color:COLORS.accent,fontSize:11,fontFamily:"monospace",flex:1}}>{validator.id}</span>
        <span style={{color:passed?COLORS.green:COLORS.orange,fontSize:12,fontWeight:"bold"}}>{(validator.score*100).toFixed(1)}%</span>
        <span style={{fontSize:14}}>{passed?"✓":"⚠"}</span>
      </div>
    </div>
  );
}

function DecisionBadge({decision}){
  const cfg={
    APPROVE:{color:COLORS.green,bg:"#001A0D",icon:"✓",label:"APROVADO"},
    REJECT:{color:COLORS.red,bg:"#1A0000",icon:"✗",label:"REJEITADO"},
    ESCALATE:{color:COLORS.orange,bg:"#1A0E00",icon:"▲",label:"ESCALADO"},
    REVISE:{color:COLORS.blue,bg:"#00101A",icon:"↻",label:"REVISÃO"},
  }[decision]||{color:COLORS.gray,bg:"#111",icon:"?",label:decision};
  return(
    <div style={{background:cfg.bg,border:`2px solid ${cfg.color}`,borderRadius:12,padding:"20px 32px",textAlign:"center",boxShadow:`0 0 24px ${cfg.color}44`}}>
      <div style={{fontSize:40,marginBottom:8}}>{cfg.icon}</div>
      <div style={{color:cfg.color,fontSize:22,fontWeight:"bold",fontFamily:"monospace"}}>{cfg.label}</div>
    </div>
  );
}

function SciencePanel(){
  const sciences=[
    {name:"Ensemble Learning",refs:"Breiman 2001; Dietterich 2000",color:COLORS.blue,desc:"Random Forests, Boosting — combinar modelos fracos em decisões fortes. Base de todos os validators ensemble."},
    {name:"Adversarial ML (AML)",refs:"Goodfellow et al. 2015; NeurIPS AdvML 2024",color:COLORS.red,desc:"Perturbações mínimas que mudam saídas do modelo. FGSM, PGD. Base dos ataques dos contra-validadores."},
    {name:"Calibration Theory",refs:"Platt 1999; Guo et al. 2017 NeurIPS",color:COLORS.green,desc:"ECE (Expected Calibration Error), Platt Scaling, Isotonic Regression. Base da camada de calibração."},
    {name:"Bayesian Decision Theory",refs:"Bernardo & Smith 2000; Murphy 2012",color:COLORS.purple,desc:"Atualização de crenças via evidências. Log-odds, prior × likelihood → posterior. Base da fusão bayesiana."},
    {name:"Monte Carlo Methods",refs:"Metropolis 1953; Basel III Stress Tests",color:COLORS.orange,desc:"Simulação estocástica de N cenários. Estimativa de média, variância e riscos de cauda. Base do World Model."},
    {name:"World Models",refs:"Ha & Schmidhuber 2018; Hafner DreamerV3 2023",color:COLORS.teal,desc:"Modelos de ambiente P(s'|s,a). RL latente: agente simula futuros internamente antes de agir."},
    {name:"Monte Carlo Tree Search",refs:"Coulom 2006; Silver et al. AlphaGo 2016",color:COLORS.gold,desc:"UCT (Upper Confidence Bound for Trees). Exploração inteligente do espaço de decisões. Base do MCTS arbiter."},
    {name:"Prospect Theory",refs:"Kahneman & Tversky 1979; Nobel Econ. 1992",color:COLORS.red,desc:"Aversão a perdas (λ=2.25), distorção de probabilidades, função de valor assimétrica. Base do risk adjustment."},
    {name:"AI Safety via Debate",refs:"Irving et al. 2018 (OpenAI)",color:"#FF6B9D",desc:"Dois agentes debatem; humano julga. Inspiração do par V/CV como dialética computacional adversarial."},
    {name:"Design de Mecanismos",refs:"Hurwicz, Maskin, Myerson — Nobel 2007",color:"#4ECDC4",desc:"Regras de incentivo que levam agentes auto-interessados a comportamento desejável. Base do meta-arbiter."},
    {name:"Meta-Learning / AutoML",refs:"Vanschoren 2019; Hospedales et al. 2022",color:"#A78BFA",desc:"'Learning to learn' — agentes de calibração aprendem a ajustar outros algoritmos automaticamente."},
    {name:"Information Theory",refs:"Shannon 1948; Cover & Thomas 2006",color:"#FFD93D",desc:"Entropia, KL Divergence, Informação Mútua. Mede riqueza informacional da evidência e redundância dos validators."},
  ];
  return(
    <div>
      {sciences.map((s,i)=>(
        <div key={i} style={{background:COLORS.midNavy,border:`1px solid ${s.color}33`,borderRadius:8,padding:"12px 14px",marginBottom:10,borderLeft:`3px solid ${s.color}`}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:6}}>
            <span style={{color:s.color,fontSize:12,fontWeight:"bold",fontFamily:"monospace"}}>{s.name}</span>
            <span style={{color:COLORS.gray,fontSize:9,fontFamily:"monospace"}}>{s.refs}</span>
          </div>
          <p style={{color:COLORS.accent,fontSize:11,margin:0,lineHeight:1.5}}>{s.desc}</p>
        </div>
      ))}
    </div>
  );
}

export default function DVCADashboard(){
  const [tab,setTab]=useState("pipeline");
  const [running,setRunning]=useState(false);
  const [animate,setAnimate]=useState(false);
  const [result,setResult]=useState(null);
  const [phase,setPhase]=useState("idle");

  const phases=["idle","calibrating","validating","counter-validating","world-model","arbitrating","done"];

  async function runPipeline(){
    setRunning(true);setAnimate(false);setResult(null);
    for(let i=1;i<phases.length;i++){
      setPhase(phases[i]);
      await new Promise(r=>setTimeout(r,[0,1200,900,900,800,600,400][i]));
    }
    setResult(simulateDVCA());setAnimate(true);setRunning(false);
  }

  const tabs=[
    {id:"pipeline",label:"⚡ Pipeline"},
    {id:"validation",label:"✓ Validação"},
    {id:"counter",label:"⚔ Contra-Val"},
    {id:"calibration",label:"⚙ Calibração"},
    {id:"science",label:"🧬 Ciências"},
  ];

  const phaseColor={
    calibrating:COLORS.orange,validating:COLORS.blue,
    "counter-validating":COLORS.red,"world-model":COLORS.purple,
    arbitrating:COLORS.gold,done:COLORS.green,idle:COLORS.gray
  }[phase];

  return(
    <div style={{background:COLORS.navy,minHeight:"100vh",fontFamily:"monospace",color:COLORS.white}}>
      {/* Header */}
      <div style={{background:"linear-gradient(135deg,#0B0B2B,#1A0A40)",borderBottom:`2px solid ${COLORS.gold}`,padding:"16px 20px"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div>
            <div style={{color:COLORS.gold,fontSize:16,fontWeight:"bold"}}>DVCA — Dual Validation / Counter-Validation Arbiter</div>
            <div style={{color:COLORS.accent,fontSize:10,marginTop:3}}>17 Algoritmos · Sync + Async · Calibração Platt · World Model · MCTS · Meta-Arbiter</div>
          </div>
          <button onClick={runPipeline} disabled={running} style={{
            background:running?"#1A1A4A":`linear-gradient(135deg,${COLORS.gold},#A07830)`,
            color:running?COLORS.gray:COLORS.navy,border:"none",borderRadius:8,
            padding:"10px 20px",fontSize:12,fontWeight:"bold",cursor:running?"not-allowed":"pointer",fontFamily:"monospace"
          }}>
            {running?`⟳ ${phase.toUpperCase()}...`:"▶ RUN PIPELINE"}
          </button>
        </div>
        {running&&(
          <div style={{marginTop:12,display:"flex",gap:6}}>
            {phases.slice(1).map((p,i)=>(
              <div key={p} style={{flex:1,height:4,borderRadius:2,background:phases.indexOf(phase)>i?phaseColor:"#1A1A4A",transition:"background 0.4s"}}/>
            ))}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{display:"flex",background:"#0D0D30",borderBottom:`1px solid #2A2A5A`,overflowX:"auto"}}>
        {tabs.map(t=>(
          <button key={t.id} onClick={()=>setTab(t.id)} style={{
            background:"none",border:"none",
            borderBottom:tab===t.id?`2px solid ${COLORS.gold}`:"2px solid transparent",
            color:tab===t.id?COLORS.gold:COLORS.gray,
            padding:"10px 16px",fontSize:11,cursor:"pointer",fontFamily:"monospace",whiteSpace:"nowrap"
          }}>{t.label}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{padding:20,maxWidth:960,margin:"0 auto"}}>

        {/* PIPELINE TAB */}
        {tab==="pipeline"&&(
          <div>
            {!result&&!running&&(
              <div style={{textAlign:"center",padding:"60px 20px",color:COLORS.gray,border:`1px dashed #2A2A5A`,borderRadius:12}}>
                <div style={{fontSize:48,marginBottom:16}}>⚡</div>
                <div style={{fontSize:14,color:COLORS.accent}}>Pressione <span style={{color:COLORS.gold}}>RUN PIPELINE</span> para executar o DVCA</div>
                <div style={{fontSize:11,marginTop:8}}>Calibração → 10 Validadores → 7 Contra-Validadores → World Model → MCTS → Meta-Arbiter</div>
              </div>
            )}
            {running&&(
              <div style={{textAlign:"center",padding:"40px 20px"}}>
                <div style={{fontSize:36,marginBottom:16,color:phaseColor}}>⟳</div>
                <div style={{color:phaseColor,fontSize:14,fontWeight:"bold"}}>{phase.toUpperCase().replace("-"," ")}</div>
              </div>
            )}
            {result&&(
              <div>
                <div style={{display:"flex",gap:16,marginBottom:20,flexWrap:"wrap"}}>
                  <div style={{flex:"0 0 auto"}}><DecisionBadge decision={result.decision}/></div>
                  <div style={{flex:1,minWidth:200,background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.gold}33`}}>
                    <div style={{color:COLORS.gold,fontSize:11,marginBottom:12,fontWeight:"bold"}}>SCORES COMPOSTOS</div>
                    <ScoreBar score={result.vFused} label="V — Validation" color={COLORS.blue} animate={animate}/>
                    <ScoreBar score={result.cvFused} label="CV — Counter-Val" color={COLORS.red} animate={animate}/>
                    <ScoreBar score={result.worldScore} label="W — World Model" color={COLORS.purple} animate={animate}/>
                    <ScoreBar score={result.composite} label="Composite (V+CV+W)" color={COLORS.gold} animate={animate}/>
                    <ScoreBar score={result.riskAdj} label="Risk-Adjusted" color={COLORS.green} animate={animate}/>
                    <div style={{marginTop:10,padding:"8px 12px",background:"#0D0D30",borderRadius:6,border:`1px solid ${result.winner==="VALIDATION"?COLORS.blue:COLORS.red}44`}}>
                      <span style={{color:COLORS.accent,fontSize:10}}>🏆 WINNER: </span>
                      <span style={{color:result.winner==="VALIDATION"?COLORS.blue:COLORS.red,fontSize:11,fontWeight:"bold"}}>{result.winner} ({(result.winScore*100).toFixed(1)}%)</span>
                    </div>
                  </div>
                </div>
                <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.gold}33`,marginBottom:20}}>
                  <div style={{color:COLORS.gold,fontSize:11,marginBottom:12,fontWeight:"bold"}}>🧠 CHAIN-OF-THOUGHT (Meta-Arbiter)</div>
                  {result.reasoning.map((step,i)=>(
                    <div key={i} style={{padding:"8px 12px",marginBottom:6,background:"#0D0D30",borderRadius:6,borderLeft:`2px solid ${COLORS.gold}66`,color:COLORS.accent,fontSize:11,lineHeight:1.5,opacity:animate?1:0,transition:`opacity 0.4s ${i*0.15}s`}}>{step}</div>
                  ))}
                </div>
                <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid #2A2A5A`}}>
                  <div style={{color:COLORS.gold,fontSize:11,marginBottom:12,fontWeight:"bold"}}>🏗 PIPELINE ARCHITECTURE</div>
                  <pre style={{fontSize:9,color:COLORS.green,margin:0,lineHeight:1.8,overflowX:"auto"}}>{
`PAYLOAD ──→ [CALIBRATION AGENTS] ──→ Fine-tune Platt(A,B) + fusion weights
 │
 ├──→ [SYNC CHAIN]   V1→V2→V3→V4→V5        (sequential propagation)
 │    [ASYNC POOL]   V6∥V7∥V8∥V9∥V10       (parallel execution)
 │    [BAYESIAN FUSION] → V_SCORE = ${(result.vFused*100).toFixed(1)}% ${result.vFused>=0.97?"✓ ≥97%":"⚠ <97%"}
 │
 ├──→ [CV SYNC]      CV1→CV2→CV3            (red-team sequential)
 │    [CV ASYNC]     CV4∥CV5∥CV6∥CV7        (adversarial attacks)
 │    [BAYESIAN FUSION] → CV_SCORE = ${(result.cvFused*100).toFixed(1)}% ${result.cvFused>=0.97?"✓ ≥97%":"⚠ <97%"}
 │
 ├──→ [WORLD MODEL]  20 trajectories × 50 steps → W = ${(result.worldScore*100).toFixed(1)}%
 │
 └──→ [META-ARBITER]
       ├─ WINNER: ${result.winner} (${(result.winScore*100).toFixed(1)}%)
       ├─ COMPOSITE: V×0.40 + CV×0.35 + W×0.25 = ${(result.composite*100).toFixed(1)}%
       ├─ PROSPECT THEORY risk adj → ${(result.riskAdj*100).toFixed(1)}%
       ├─ MCTS 200 simulations (UCT c=√2)
       └─ FINAL DECISION: ${result.decision}`}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* VALIDATION TAB */}
        {tab==="validation"&&result&&(
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
            <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.blue}33`}}>
              <div style={{color:COLORS.blue,fontSize:11,marginBottom:10,fontWeight:"bold"}}>SYNC CHAIN (V1-V5) — {(result.vSync*100).toFixed(1)}%</div>
              {result.syncValidators.map((v,i)=><ValidatorCard key={v.id} validator={v} index={i} animate={animate}/>)}
            </div>
            <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.teal}33`}}>
              <div style={{color:COLORS.teal,fontSize:11,marginBottom:10,fontWeight:"bold"}}>ASYNC POOL (V6-V10) — {(result.vAsync*100).toFixed(1)}%</div>
              {result.asyncValidators.map((v,i)=><ValidatorCard key={v.id} validator={v} index={i} animate={animate}/>)}
            </div>
          </div>
        )}

        {/* COUNTER TAB */}
        {tab==="counter"&&result&&(
          <div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:16}}>
              <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.red}33`}}>
                <div style={{color:COLORS.red,fontSize:11,marginBottom:10,fontWeight:"bold"}}>SYNC RED-TEAM (CV1-CV3)</div>
                {result.cvSync.map((v,i)=><ValidatorCard key={v.id} validator={v} index={i} animate={animate}/>)}
              </div>
              <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.orange}33`}}>
                <div style={{color:COLORS.orange,fontSize:11,marginBottom:10,fontWeight:"bold"}}>ASYNC ATTACKS (CV4-CV7)</div>
                {result.cvAsync.map((v,i)=><ValidatorCard key={v.id} validator={v} index={i} animate={animate}/>)}
              </div>
            </div>
            <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.red}33`}}>
              <div style={{color:COLORS.red,fontSize:11,marginBottom:12,fontWeight:"bold"}}>🗺 VULNERABILITY MAP</div>
              {Object.entries(result.vuln).sort((a,b)=>b[1]-a[1]).map(([id,score])=>(
                <div key={id} style={{marginBottom:8}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                    <span style={{color:COLORS.accent,fontSize:10,fontFamily:"monospace"}}>{id}</span>
                    <span style={{color:score>0.1?COLORS.red:score>0.05?COLORS.orange:COLORS.green,fontSize:10,fontWeight:"bold"}}>{(score*100).toFixed(2)}%</span>
                  </div>
                  <div style={{height:6,background:"#1A1A4A",borderRadius:3}}>
                    <div style={{height:"100%",borderRadius:3,background:score>0.1?COLORS.red:score>0.05?COLORS.orange:COLORS.green,width:`${Math.min(score*1000,100)}%`}}/>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CALIBRATION TAB */}
        {tab==="calibration"&&result&&(
          <div style={{background:COLORS.midNavy,borderRadius:10,padding:16,border:`1px solid ${COLORS.green}33`}}>
            <div style={{color:COLORS.green,fontSize:11,marginBottom:12,fontWeight:"bold"}}>⚙ ECE CALIBRATION — Expected Calibration Error Before → After Platt Scaling</div>
            {result.calReports.map((r,i)=>{
              const imp=((r.eceBefore-r.eceAfter)/r.eceBefore*100).toFixed(0);
              const pos=imp>0;
              return(
                <div key={i} style={{marginBottom:12}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                    <span style={{color:COLORS.accent,fontSize:10,fontFamily:"monospace"}}>{r.id}</span>
                    <span style={{color:pos?COLORS.green:COLORS.red,fontSize:10}}>ECE: {r.eceBefore.toFixed(3)}→{r.eceAfter.toFixed(3)} ({pos?"+":""}{imp}%)</span>
                  </div>
                  <div style={{display:"flex",gap:4}}>
                    <div style={{flex:r.eceBefore,height:5,background:COLORS.red,borderRadius:3}}/>
                    <div style={{flex:1-r.eceBefore,height:5,background:"#1A1A4A",borderRadius:3}}/>
                  </div>
                  <div style={{display:"flex",gap:4,marginTop:2}}>
                    <div style={{flex:r.eceAfter,height:5,background:COLORS.green,borderRadius:3}}/>
                    <div style={{flex:1-r.eceAfter,height:5,background:"#1A1A4A",borderRadius:3}}/>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* SCIENCE TAB */}
        {tab==="science"&&<SciencePanel/>}

        {/* Empty state */}
        {tab!=="pipeline"&&tab!=="science"&&!result&&(
          <div style={{textAlign:"center",padding:"40px",color:COLORS.gray}}>
            Execute o pipeline primeiro ▶
          </div>
        )}
      </div>
    </div>
  );
}
