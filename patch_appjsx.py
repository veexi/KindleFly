#!/usr/bin/env python3
# patch_appjsx.py - replaces the login-portal block with a unified guest+logged-in recommendations view

import re

fp = 'frontend/src/App.jsx'
with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '                {/* Account details or login portal */}'
# The end marker is everything up to (but NOT including) the closing </div>\n)}\n</div>\n)}\n\n{/* TAB 2
end_marker = '                )}\n              </div>\n            )}\n          </div>\n        )}\n\n        {/* TAB 2'

si = content.find(start_marker)
ei = content.find(end_marker, si)

if si < 0 or ei < 0:
    print(f'ERROR: markers not found (si={si}, ei={ei})')
    exit(1)

# The new block replaces everything from si to ei (exclusive — we keep the end_marker)
new_block = '''                {/* Unified recommendations section — shown for all users */}
                <div className="zlib-home-recommendations">
                  <div className="section-title-container">
                    <h3 className="section-title" style={{ margin: 0 }}>
                      {zlibStatus.logged_in ? '猜你喜欢 / 账户个人推荐' : '热门推荐书籍'}
                    </h3>
                    {zlibStatus.logged_in && (
                      <button className="refresh-rec-btn" onClick={fetchRecommendations} title="刷新推荐" disabled={recLoading}>
                        <RefreshCw className={`btn-icon ${recLoading ? 'spinner' : ''}`} style={{ width: '14px', height: '14px' }} />
                      </button>
                    )}
                  </div>

                  {/* Guest mode banner */}
                  {!zlibStatus.logged_in && (
                    <div className="guest-mode-banner">
                      <span>以下为热门经典书籍展示。登录后可获取个人推荐、搜索及一键推送功能。</span>
                      <button className="btn-link" onClick={() => setShowLoginModal(true)}>立即登录</button>
                    </div>
                  )}

                  {recLoading && (!displayedRecommendations || displayedRecommendations.length === 0) ? (
                    <div className="rec-loading-grid">
                      {[1, 2, 3, 4].map(i => (
                        <div key={i} className="book-card skeleton-card">
                          <div className="book-cover skeleton-element" />
                          <div className="book-info-container">
                            <div className="skeleton-line title" />
                            <div className="skeleton-line author" />
                            <div className="skeleton-line meta" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : recError ? (
                    <div className="rec-error-box">
                      <span>获取推荐图书失败：{recError}</span>
                      {zlibStatus.logged_in && (
                        <button className="btn btn-secondary" onClick={fetchRecommendations} style={{ padding: '4px 10px', fontSize: '11px' }}>
                          重试
                        </button>
                      )}
                    </div>
                  ) : displayedRecommendations && displayedRecommendations.length > 0 ? (
                    <div className="recommendations-scroll-container">
                      <div className="recommendations-grid">
                        {displayedRecommendations.map((book) => {
                          const bookId = book.id;
                          const pushingState = pushingBooks[bookId];
                          return (
                            <div key={bookId} className="book-card rec-book-card">
                              <div className="book-cover" onClick={() => handleOpenBookDetails(book)} style={{ cursor: 'pointer' }}>
                                {covers[bookId] ? (
                                  <img src={covers[bookId]} alt={book.title} />
                                ) : book.cover ? (
                                  <img src={book.cover} alt={book.title} onError={(e) => { e.target.style.display = 'none'; }} />
                                ) : (
                                  <BookOpen style={{ width: '24px', height: '24px', opacity: 0.3 }} />
                                )}
                              </div>
                              <div className="book-info-container">
                                <div onClick={() => handleOpenBookDetails(book)} style={{ display: 'flex', flexDirection: 'column', minWidth: 0, cursor: 'pointer' }}>
                                  <span className="book-title" title={book.title}>{book.title}</span>
                                  <span className="book-author" title={book.author}>{book.author || '未知'}</span>
                                  <div className="book-meta">
                                    <span className="badge badge-format">{book.extension}</span>
                                    <span className="badge badge-size">{book.filesizeString || '未知'}</span>
                                  </div>
                                </div>
                                <div className="push-btn-container" style={{ marginTop: '6px' }}>
                                  {!zlibStatus.logged_in ? (
                                    <button
                                      className="btn btn-secondary"
                                      style={{ width: '100%', fontSize: '10px', padding: '4px 0' }}
                                      onClick={() => setShowLoginModal(true)}
                                    >
                                      登录后操作
                                    </button>
                                  ) : (
                                    <>
                                      {pushingState === 'downloading' && (
                                        <button className="btn btn-secondary" style={{ width: '100%', fontSize: '10px', padding: '4px 0' }} disabled>
                                          <Spinner /> 下载中
                                        </button>
                                      )}
                                      {pushingState === 'pushing' && (
                                        <button className="btn btn-secondary" style={{ width: '100%', fontSize: '10px', padding: '4px 0' }} disabled>
                                          <Spinner /> 推送中
                                        </button>
                                      )}
                                      {pushingState === 'success' && (
                                        <button className="btn btn-secondary" style={{ width: '100%', fontSize: '10px', padding: '4px 0', border: '1px solid rgba(16, 185, 129, 0.4)', color: 'var(--accent-green)' }} disabled>
                                          <CheckCircle style={{ width: '10px', height: '10px' }} /> 已推送
                                        </button>
                                      )}
                                      {(!pushingState || pushingState.status === 'error') && (
                                        <button
                                          className="btn btn-primary"
                                          style={{ width: '100%', fontSize: '10px', padding: '4px 0' }}
                                          onClick={() => handleCheckAndPushBook(book)}
                                        >
                                          <Download style={{ width: '10px', height: '10px' }} /> 推送 Kindle
                                        </button>
                                      )}
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Load More button — only for logged-in users */}
                      {zlibStatus.logged_in && (
                        <div className="load-more-container">
                          <button className="btn-load-more" onClick={handleLoadMoreRecommendations} disabled={loadMoreLoading}>
                            {loadMoreLoading ? <Spinner /> : null}
                            {loadMoreLoading ? '正在加载...' : '显示更多推荐与热门图书'}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="rec-empty-box">
                      <span>暂无书籍数据。</span>
                    </div>
                  )}
                </div>
'''

new_content = content[:si] + new_block + content[ei:]

with open(fp, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'SUCCESS: replaced {ei - si} chars at position {si} with {len(new_block)} chars')
