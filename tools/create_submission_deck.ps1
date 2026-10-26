$ErrorActionPreference = 'Stop'

$outDir = Join-Path (Get-Location) 'submission'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path $outDir 'ReleaseProof_AI_Hackathon_Deck.pptx'
if (Test-Path $out) { Remove-Item -LiteralPath $out -Force }

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $false
$pres = $ppt.Presentations.Add()
$pres.PageSetup.SlideWidth = (Pt 13.333)
$pres.PageSetup.SlideHeight = (Pt 7.5)

$W = 13.333
$H = 7.5
$navy = 0x16131F
$ink = 0xF5F1E8
$muted = 0xB7B0A6
$lime = 0xB7FF3C
$violet = 0x9B7BFF
$coral = 0xFF8066
$teal = 0x67E8D3
$dark = 0x0D0B12

function Pt($n) { return $n * 72 }
function AddText($slide, $text, $x, $y, $w, $h, $size, $color, $bold=$false, $font='Aptos') {
  $shape = $slide.Shapes.AddTextbox(1, (Pt $x), (Pt $y), (Pt $w), (Pt $h))
  $shape.TextFrame2.TextRange.Text = $text
  $shape.TextFrame2.TextRange.Font.Name = $font
  $shape.TextFrame2.TextRange.Font.Size = $size
  $shape.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = $color
  $shape.TextFrame2.TextRange.Font.Bold = [int]$bold
  $shape.TextFrame2.WordWrap = $true
  $shape.TextFrame2.MarginLeft = 0
  $shape.TextFrame2.MarginRight = 0
  $shape.TextFrame2.MarginTop = 0
  $shape.TextFrame2.MarginBottom = 0
  return $shape
}
function AddRect($slide, $x, $y, $w, $h, $fill, $line=$fill, $radius=$false) {
  $type = if ($radius) { 5 } else { 1 }
  $s = $slide.Shapes.AddShape($type, (Pt $x), (Pt $y), (Pt $w), (Pt $h))
  $s.Fill.ForeColor.RGB = $fill
  $s.Line.ForeColor.RGB = $line
  $s.Line.Transparency = 1
  return $s
}
function AddLine($slide, $x1, $y1, $x2, $y2, $color, $weight=1.5) {
  $l = $slide.Shapes.AddLine((Pt $x1), (Pt $y1), (Pt $x2), (Pt $y2))
  $l.Line.ForeColor.RGB = $color
  $l.Line.Weight = $weight
  return $l
}
function Base($slide, $num, $section) {
  $slide.Background.Fill.ForeColor.RGB = $navy
  AddRect $slide 0 0 13.333 0.12 $lime
  AddText $slide 'RELEASEPROOF AI' 0.55 7.08 2.5 0.18 8 $muted $true
  AddText $slide $section 9.4 7.08 2.9 0.18 8 $muted $false
  AddText $slide ('0' + $num) 12.55 7.05 0.35 0.2 9 $lime $true
}
function Pill($slide, $text, $x, $y, $w, $color) {
  AddRect $slide $x $y $w 0.3 $color $color $true | Out-Null
  AddText $slide $text ($x+0.12) ($y+0.06) ($w-0.24) 0.16 8 $dark $true | Out-Null
}

# 1 Cover
$s = $pres.Slides.Add(1, 12); Base $s 1 'HACKATHON SUBMISSION'
AddText $s 'Every release should\nshow its work.' 0.7 1.15 7.1 1.5 30 $ink $true
AddText $s 'ReleaseProof AI' 0.72 3.15 5.5 0.48 20 $lime $true
AddText $s 'Evidence-driven release intelligence for Copado Agentia' 0.74 3.8 6.9 0.35 14 $muted
AddRect $s 8.45 1.05 3.65 4.8 $dark $dark $true | Out-Null
AddText $s 'RELEASE\nDECISION' 8.85 1.52 2.8 0.55 13 $muted $true
AddText $s 'INSUFFICIENT' 8.85 2.3 2.8 0.35 18 $coral $true
AddLine $s 8.85 2.9 11.72 2.9 $muted 0.7 | Out-Null
AddText $s 'Boundary case missing\nPermission check stale\nEvidence export ready' 8.85 3.25 2.8 1.1 13 $ink
Pill $s 'LOCAL DEMO' 8.85 5.08 1.35 $lime
AddText $s 'A transparent layer around Plan → Build → Test' 0.74 5.75 6.4 0.3 12 $teal

# 2 Problem
$s = $pres.Slides.Add(2, 12); Base $s 2 'THE GAP'
AddText $s 'Green tests can still miss the business rule' 0.7 0.75 10.6 0.55 24 $ink $true
AddText $s 'Teams can ship a passing build without proving the behavior that matters.' 0.72 1.48 10.5 0.3 13 $muted
AddText $s 'WHAT TYPICAL RELEASE SIGNALS SHOW' 0.72 2.25 4.8 0.2 9 $muted $true
AddText $s '✓ happy path passes\n✓ build is green\n✓ deployment is available' 0.72 2.62 4.5 1.25 18 $ink
AddText $s 'WHAT THEY CAN MISS' 6.9 2.25 4.8 0.2 9 $coral $true
AddText $s '× boundary equality\n× permission behavior\n× evidence invalidated by a change' 6.9 2.62 5.4 1.25 18 $ink
AddLine $s 0.72 4.35 12.45 4.35 $muted 0.6 | Out-Null
AddText $s 'ReleaseProof makes the missing proof visible before approval.' 0.72 4.75 9.9 0.45 22 $lime $true
AddText $s 'The product does not replace Copado. It makes the release decision explainable.' 0.72 5.55 10.6 0.3 13 $muted

# 3 Use case
$s = $pres.Slides.Add(3, 12); Base $s 3 'USE CASE'
AddText $s 'US-247: lead routing at the equality boundary' 0.7 0.75 11.5 0.5 23 $ink $true
AddText $s 'Business contract' 0.72 1.55 2.3 0.22 10 $lime $true
AddText $s 'Score greater than 80 → Senior Sales\nScore 80 or below → Standard Sales\nOnly Sales Managers can override' 0.72 1.92 5.5 1.3 17 $ink
AddText $s 'Existing examples' 7.05 1.55 2.5 0.22 10 $violet $true
AddText $s '60 → Standard Sales\n100 → Senior Sales' 7.05 1.92 4.5 0.75 17 $ink
AddText $s 'Missing proof' 0.72 4.05 2.3 0.22 10 $coral $true
AddText $s 'The suite omits score = 80 and does not verify the override permission.' 0.72 4.42 9.9 0.45 20 $coral $true
AddText $s 'That is the exact gap ReleaseProof surfaces.' 0.72 5.33 8.8 0.3 14 $muted

# 4 Demo journey
$s = $pres.Slides.Add(4, 12); Base $s 4 'LIVE DEMO STORY'
AddText $s 'One change. One decision. A reason judges can see.' 0.7 0.75 11.8 0.5 23 $ink $true
$xs = @(0.8, 4.55, 8.3); $titles = @('1  ANALYZE','2  CHECK','3  RE-RUN'); $body = @('Evidence incomplete\n\nThe contract needs a boundary check.','80 -> Senior Sales\n\nThe modeled behavior fails the equality case.','Evidence satisfied\n\nThe boundary fix closes the gap.'); $cols=@($violet,$coral,$lime)
for($i=0;$i -lt 3;$i++){ AddRect $s $xs[$i] 1.8 3.15 3.5 $dark $dark $true | Out-Null; AddText $s $titles[$i] ($xs[$i]+0.28) 2.18 2.5 0.22 10 $cols[$i] $true; AddText $s $body[$i] ($xs[$i]+0.28) 2.72 2.55 1.5 17 $ink; if($i -lt 2){ AddText $s '->' ($xs[$i]+3.32) 3.12 0.35 0.35 22 $muted $true } }
AddText $s 'The screen recording follows this exact sequence in LOCAL DEMO mode.' 0.8 5.95 10.8 0.3 13 $teal

# 5 Product
$s = $pres.Slides.Add(5, 12); Base $s 5 'PRODUCT'
AddText $s 'The evidence ledger keeps the release honest' 0.7 0.75 11.5 0.5 23 $ink $true
AddText $s 'INPUT' 0.75 1.72 1.1 0.2 9 $muted $true
AddText $s 'Business contract\nwork item\ntarget environment' 0.75 2.08 2.7 1.1 17 $ink
AddText $s 'EVIDENCE' 4.42 1.72 1.5 0.2 9 $muted $true
AddText $s 'required checks\npass / fail / stale\nreason for confidence' 4.42 2.08 2.9 1.1 17 $ink
AddText $s 'DECISION' 8.2 1.72 1.3 0.2 9 $muted $true
AddText $s 'satisfied\ninsufficient\nneeds new evidence' 8.2 2.08 3.1 1.1 17 $ink
AddLine $s 3.35 2.65 4.15 2.65 $lime 2 | Out-Null; AddLine $s 7.05 2.65 7.9 2.65 $lime 2 | Out-Null
AddRect $s 0.75 4.42 10.8 1.15 $dark $dark $true | Out-Null
AddText $s 'Exportable proof' 1.05 4.72 2.1 0.22 11 $lime $true
AddText $s 'Every decision carries its checks, evidence version, assumptions, and limitations.' 3.2 4.7 7.7 0.3 15 $ink

# 6 Architecture
$s = $pres.Slides.Add(6, 12); Base $s 6 'ARCHITECTURE'
AddText $s 'A local-first engine with a live Copado path' 0.7 0.75 11.8 0.5 23 $ink $true
AddRect $s 0.8 1.8 3.25 3.85 $dark $dark $true | Out-Null
AddText $s 'RELEASEPROOF CORE' 1.1 2.15 2.5 0.22 10 $lime $true
AddText $s 'React / Next.js PWA\nFastAPI backend\nDeterministic evidence engine\nExportable JSON ledger' 1.1 2.65 2.5 1.5 17 $ink
AddRect $s 5.02 1.8 3.25 3.85 $dark $dark $true | Out-Null
AddText $s 'AGENTIA ADAPTER' 5.32 2.15 2.5 0.22 10 $violet $true
AddText $s 'CLI capability probe\nCICD work item context\nLocal quality gates\nCRT build polling' 5.32 2.65 2.5 1.5 17 $ink
AddRect $s 9.25 1.8 3.25 3.85 $dark $dark $true | Out-Null
AddText $s 'COPADO SERVICES' 9.55 2.15 2.5 0.22 10 $teal $true
AddText $s 'Pipelines and work items\nSalesforce environments\nCopado Robotic Testing\nAI and org context' 9.55 2.65 2.5 1.5 17 $ink
AddLine $s 4.08 3.7 4.92 3.7 $lime 2 | Out-Null; AddLine $s 8.3 3.7 9.15 3.7 $lime 2 | Out-Null
AddText $s 'Local mode is fully reproducible. Live mode activates when the Copado organization is connected.' 0.8 6.12 11.2 0.3 13 $muted

# 7 Novelty
$s = $pres.Slides.Add(7, 12); Base $s 7 'WHY IT MATTERS'
AddText $s 'The novelty is the decision layer' 0.7 0.75 10.8 0.5 24 $ink $true
AddText $s 'ReleaseProof adds the missing connection between intent and evidence.' 0.72 1.48 10.5 0.3 13 $muted
AddText $s '1' 0.78 2.3 0.4 0.45 28 $lime $true; AddText $s 'Business-aware checks' 1.45 2.32 3.3 0.26 16 $ink $true; AddText $s 'Tests map back to the contract, not only to code coverage.' 1.45 2.75 4.7 0.35 12 $muted
AddText $s '2' 0.78 3.65 0.4 0.45 28 $violet $true; AddText $s 'Evidence has a lifecycle' 1.45 3.67 3.3 0.26 16 $ink $true; AddText $s 'A change can make yesterday’s proof stale.' 1.45 4.1 4.7 0.35 12 $muted
AddText $s '3' 6.8 2.3 0.4 0.45 28 $coral $true; AddText $s 'Explainable release gates' 7.47 2.32 4.5 0.26 16 $ink $true; AddText $s 'The decision includes the reason and the next action.' 7.47 2.75 4.7 0.35 12 $muted
AddText $s '4' 6.8 3.65 0.4 0.45 28 $teal $true; AddText $s 'Local-first, integration-ready' 7.47 3.67 4.7 0.26 16 $ink $true; AddText $s 'Teams can prove behavior before credentials are available.' 7.47 4.1 4.7 0.35 12 $muted

# 8 Close
$s = $pres.Slides.Add(8, 12); Base $s 8 'TAKEAWAY'
AddText $s 'Ship with evidence,\nnot assumptions.' 0.75 1.0 7.2 1.3 30 $ink $true
AddText $s 'ReleaseProof AI' 0.78 2.85 4.2 0.3 18 $lime $true
AddText $s 'A practical release intelligence layer for Copado Agentia.' 0.8 3.4 7.3 0.35 14 $muted
AddRect $s 8.4 1.35 3.5 3.5 $lime $lime $true | Out-Null
AddText $s 'JUDGE\nTAKEAWAY' 8.82 1.78 2.7 0.45 12 $dark $true
AddText $s 'Did we prove\nthe contract?' 8.82 2.65 2.7 0.75 22 $dark $true
AddText $s 'Demo: localhost:3000\nMode: LOCAL DEMO\nLive adapter: Agentia / CRT ready' 0.8 5.2 5.8 0.85 13 $teal
AddText $s 'Thank you' 8.82 5.6 2.5 0.3 16 $ink $true

$pres.SaveAs($out)
$pres.Close(); $ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($pres) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
Write-Output $out
