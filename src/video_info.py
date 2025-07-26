def show_video_info(st, info):
    # Show thumbnail image (clickable to open video)
    thumbnail_url = info.get('thumbnail')
    video_url = info.get('webpage_url')
    video_id = info.get('id')

    # if thumbnail_url:
    #     st.markdown(f"[![Thumbnail]({thumbnail_url})]({video_url})")
    
    st.markdown(
    f"""
    <style>
    .video-container {{
        position: relative;
        padding-bottom: 56.25%;
        height: 0;
        overflow: hidden;
        max-width: 100%;
    }}
    .video-container iframe {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }}
    </style>
    <div class="video-container">
        <iframe src="https://www.youtube.com/embed/{video_id}"
            frameborder="0"
            allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
        </iframe>
    </div>
    """,
    unsafe_allow_html=True
)


    # Title as a clickable link
    title = info.get('title', 'No title found')
    st.markdown(f"### [{title}]({video_url})")
    
    ycol1, ycol2, ycol3 = st.columns(3)
    with ycol1:
        channel_logo = info.get('channel_favicon')
        if channel_logo:
            st.image(channel_logo, width=50)
        st.write(info.get('uploader'))
    with ycol2:
        st.write(f"⌗ {info.get('view_count'):,}")
    with ycol3:
        st.write(f"♥️ {info.get('like_count'):,}")
    # Description (trimmed to first 300 chars)
    description = info.get('description', '')
    upload_date = info.get('upload_date')
    from datetime import datetime
    upload_date = datetime.strptime(upload_date, '%Y%m%d').strftime('%B %d, %Y')
    st.write(f"🗓️ {upload_date}")    
    if description:
        st.write(description[:300] + ('...' if len(description) > 300 else ''))
