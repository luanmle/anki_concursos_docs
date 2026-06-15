param(
    [switch]$Push
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $repositoryRoot
try {
    if (git status --porcelain) {
        throw "Commit or stash the worktree before generating admin-deploy."
    }

    Push-Location "admin"
    try {
        npm ci
        npm run lint
        npm test
        npm run build
    }
    finally {
        Pop-Location
    }

    git branch -D admin-deploy 2>$null
    git subtree split --prefix=admin --branch admin-deploy

    if ($Push) {
        git push origin admin-deploy --force
    }
    else {
        Write-Output "Branch admin-deploy generated locally. Use -Push to publish it."
    }
}
finally {
    Pop-Location
}
