import { execSync } from 'child_process'
import type { Plugin } from 'vite'

// 获取 git commit 数量（用作开发版本号）
function getGitCommitCount(): number {
  try {
    return parseInt(execSync('git rev-list --count HEAD', { encoding: 'utf-8' }).trim())
  } catch {
    return 0
  }
}

// 获取短 commit hash
function getGitShortHash(): string {
  try {
    return execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim()
  } catch {
    return 'unknown'
  }
}

// 读取 package.json 版本
function getPackageVersion(): string {
  try {
    const pkg = JSON.parse(
      require('fs').readFileSync('./package.json', 'utf-8')
    )
    return pkg.version || '0.0.0'
  } catch {
    return '0.0.0'
  }
}

export function versionPlugin(): Plugin {
  const isDev = process.env.NODE_ENV !== 'production'
  const packageVersion = getPackageVersion()
  const commitCount = getGitCommitCount()
  const commitHash = getGitShortHash()

  // 开发版本: 1.0.0-dev.123, 正式版本: 1.0.0
  const appVersion = isDev ? `${packageVersion}-dev.${commitCount}` : packageVersion
  const buildTimestamp = Date.now().toString()
  const buildMode = isDev ? 'development' : 'production'

  return {
    name: 'vite-version-plugin',
    enforce: 'pre',
    transform(code, id) {
      // 只处理 version.ts 文件
      if (id.endsWith('version.ts') || id.endsWith('version.js')) {
        return code
          .replace(/'__APP_VERSION__'/g, `'${appVersion}'`)
          .replace(/'__BUILD_TIMESTAMP__'/g, `'${buildTimestamp}'`)
          .replace(/'__BUILD_MODE__'/g, `'${buildMode}'`)
          .replace(/'__GIT_COMMIT_HASH__'/g, `'${commitHash}'`)
          .replace(/'__GIT_COMMIT_COUNT__'/g, `'${commitCount}'`)
      }
    }
  }
}
