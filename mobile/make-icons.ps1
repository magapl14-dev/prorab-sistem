# Generate Android launcher icons for WELL DOM
# Creates a flat orange square with white "W" letter, plus circular variant.
# Then resizes for every mipmap density.

Add-Type -AssemblyName System.Drawing

$ROOT = "$PSScriptRoot\android\app\src\main\res"
$ACCENT = [System.Drawing.Color]::FromArgb(255, 224, 120, 32)  # var(--orange) #e07820

function New-Icon([int]$size, [bool]$round) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias

    if ($round) {
        $g.Clear([System.Drawing.Color]::Transparent)
        $brush = New-Object System.Drawing.SolidBrush($ACCENT)
        $g.FillEllipse($brush, 0, 0, $size, $size)
        $brush.Dispose()
    } else {
        $g.Clear($ACCENT)
    }

    $fontSize = [int]($size * 0.55)
    $font = New-Object System.Drawing.Font("Arial Black", $fontSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF(0, [single]($size * -0.04), $size, $size)
    $g.DrawString("W", $font, [System.Drawing.Brushes]::White, $rect, $sf)
    $font.Dispose()
    $g.Dispose()
    return $bmp
}

function New-Foreground([int]$size) {
    # Adaptive icon foreground: transparent background, big "W" in safe area
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    $g.Clear([System.Drawing.Color]::Transparent)
    # Adaptive icon safe area is 66dp out of 108dp = ~61%
    $fontSize = [int]($size * 0.38)
    $font = New-Object System.Drawing.Font("Arial Black", $fontSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF(0, [single]($size * -0.03), $size, $size)
    $g.DrawString("W", $font, [System.Drawing.Brushes]::White, $rect, $sf)
    $font.Dispose()
    $g.Dispose()
    return $bmp
}

# Densities: mdpi=48, hdpi=72, xhdpi=96, xxhdpi=144, xxxhdpi=192
$densities = @{
    "mipmap-mdpi"    = 48
    "mipmap-hdpi"    = 72
    "mipmap-xhdpi"   = 96
    "mipmap-xxhdpi"  = 144
    "mipmap-xxxhdpi" = 192
}

# Foreground for adaptive icons uses 108dp base
$foregroundSizes = @{
    "mipmap-mdpi"    = 108
    "mipmap-hdpi"    = 162
    "mipmap-xhdpi"   = 216
    "mipmap-xxhdpi"  = 324
    "mipmap-xxxhdpi" = 432
}

foreach ($d in $densities.Keys) {
    $dir = Join-Path $ROOT $d
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $size = $densities[$d]

    $sq = New-Icon $size $false
    $sq.Save((Join-Path $dir "ic_launcher.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $sq.Dispose()

    $cir = New-Icon $size $true
    $cir.Save((Join-Path $dir "ic_launcher_round.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $cir.Dispose()

    $fg = New-Foreground $foregroundSizes[$d]
    $fg.Save((Join-Path $dir "ic_launcher_foreground.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $fg.Dispose()

    Write-Host "OK  $d  $size px"
}

# Update background color for adaptive icon (overrides drawable/ic_launcher_background.xml)
$bgXml = @'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#e07820</color>
</resources>
'@
Set-Content -Path (Join-Path $ROOT "values\ic_launcher_background.xml") -Value $bgXml -Encoding UTF8

# Replace adaptive icon xml so foreground uses PNG not vector
$adaptiveXml = @'
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
'@
Set-Content -Path (Join-Path $ROOT "mipmap-anydpi-v26\ic_launcher.xml") -Value $adaptiveXml -Encoding UTF8
Set-Content -Path (Join-Path $ROOT "mipmap-anydpi-v26\ic_launcher_round.xml") -Value $adaptiveXml -Encoding UTF8

# Delete old vector foreground if exists
$oldVector = Join-Path $ROOT "drawable-v24\ic_launcher_foreground.xml"
if (Test-Path $oldVector) { Remove-Item $oldVector -Force }

Write-Host "`nDone. Иконки сгенерированы в res/mipmap-*/"
