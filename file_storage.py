"""
Module quản lý Notes và Documents bằng file text
"""
import os
import json
from datetime import datetime

class FileStorage:
    def __init__(self, notes_dir='data/notes', docs_dir='data/docs', metadata_file='data/metadata.json', uploads_dir='uploads'):
        # Chuẩn hóa tất cả đường dẫn thành absolute path để đảm bảo lưu đúng vị trí
        self.notes_dir = os.path.abspath(os.path.normpath(notes_dir))
        self.docs_dir = os.path.abspath(os.path.normpath(docs_dir))
        self.metadata_file = os.path.abspath(os.path.normpath(metadata_file))
        self.uploads_dir = os.path.abspath(os.path.normpath(uploads_dir))
        self.notes_uploads_dir = os.path.abspath(os.path.normpath(os.path.join(self.uploads_dir, 'notes')))
        self.docs_uploads_dir = os.path.abspath(os.path.normpath(os.path.join(self.uploads_dir, 'docs')))
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(self.notes_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(self.notes_uploads_dir, exist_ok=True)
        os.makedirs(self.docs_uploads_dir, exist_ok=True)
        metadata_dir = os.path.dirname(self.metadata_file)
        if metadata_dir:
            os.makedirs(metadata_dir, exist_ok=True)
        
        # Khởi tạo metadata file nếu chưa tồn tại
        if not os.path.exists(self.metadata_file):
            self._save_metadata({'notes': [], 'docs': []})
    
    def _load_metadata(self):
        """Load metadata từ file JSON"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'notes': [], 'docs': []}
    
    def _save_metadata(self, metadata):
        """Lưu metadata vào file JSON"""
        try:
            # Đảm bảo thư mục tồn tại
            metadata_dir = os.path.dirname(self.metadata_file)
            if metadata_dir:
                os.makedirs(metadata_dir, exist_ok=True)
            
            # Ghi file với atomic write (ghi vào file tạm trước)
            temp_file = self.metadata_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Thay thế file cũ bằng file mới (os.replace hoạt động trên cả Windows và Linux từ Python 3.3+)
            # os.replace() là atomic và tương thích đa nền tảng
            os.replace(temp_file, self.metadata_file)
        except Exception as e:
            # Nếu có lỗi, xóa file tạm nếu tồn tại
            temp_file = self.metadata_file + '.tmp'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise Exception(f"Không thể lưu metadata: {str(e)}")
    
    def get_next_id(self, item_type='note'):
        """Lấy ID tiếp theo"""
        metadata = self._load_metadata()
        items = metadata.get(item_type + 's', [])
        if not items:
            return 1
        return max(int(item['id']) for item in items) + 1
    
    # === NOTES METHODS ===
    def create_note(self, title, content, category='general', user_id=None):
        """Tạo note mới"""
        note_id = self.get_next_id('note')
        
        # Đảm bảo thư mục tồn tại
        os.makedirs(self.notes_dir, exist_ok=True)
        
        # Lưu nội dung vào file text
        filename = f"{note_id}.txt"
        filepath = os.path.join(self.notes_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Không thể tạo file ghi chú: {str(e)}")
        
        # Thêm metadata
        metadata = self._load_metadata()
        note_meta = {
            'id': note_id,
            'title': title,
            'filename': filename,
            'category': category,
            'user_id': user_id,
            'attachments': [],  # Danh sách file đính kèm
            'view_count': 0,  # Số lần xem (để sắp xếp theo độ phổ biến)
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        metadata['notes'].append(note_meta)
        self._save_metadata(metadata)
        
        return self.get_note(note_id)
    
    def get_note(self, note_id):
        """Lấy note theo ID"""
        metadata = self._load_metadata()
        for note_meta in metadata.get('notes', []):
            if note_meta['id'] == int(note_id):
                # Đọc nội dung từ file
                filepath = os.path.join(self.notes_dir, note_meta['filename'])
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    return Note(
                        id=note_meta['id'],
                        title=note_meta['title'],
                        content=content,
                        category=note_meta.get('category', 'general'),
                        user_id=note_meta.get('user_id'),
                        attachments=note_meta.get('attachments', []),
                        view_count=note_meta.get('view_count', 0),
                        created_at=datetime.fromisoformat(note_meta['created_at']),
                        updated_at=datetime.fromisoformat(note_meta.get('updated_at', note_meta['created_at'])),
                        updated_by=note_meta.get('updated_by')
                    )
        return None
    
    def get_all_notes(self, category=None, search_query=None):
        """Lấy tất cả notes (có thể filter)"""
        metadata = self._load_metadata()
        notes = []
        
        for note_meta in metadata.get('notes', []):
            # Filter theo category
            if category and category != 'all' and note_meta.get('category') != category:
                continue
            
            # Đọc nội dung
            filepath = os.path.join(self.notes_dir, note_meta['filename'])
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Filter theo search query
                if search_query:
                    if search_query.lower() not in note_meta['title'].lower() and \
                       search_query.lower() not in content.lower():
                        continue
                
                note = Note(
                    id=note_meta['id'],
                    title=note_meta['title'],
                    content=content,
                    category=note_meta.get('category', 'general'),
                    user_id=note_meta.get('user_id'),
                    attachments=note_meta.get('attachments', []),
                    view_count=note_meta.get('view_count', 0),
                    created_at=datetime.fromisoformat(note_meta['created_at']),
                    updated_at=datetime.fromisoformat(note_meta.get('updated_at', note_meta['created_at'])),
                    updated_by=note_meta.get('updated_by')
                )
                notes.append(note)
        
        # Sắp xếp theo updated_at giảm dần
        notes.sort(key=lambda x: x.updated_at, reverse=True)
        return notes
    
    def increment_note_view_count(self, note_id):
        """Tăng số lần xem của note"""
        metadata = self._load_metadata()
        for note_meta in metadata.get('notes', []):
            if note_meta['id'] == int(note_id):
                note_meta['view_count'] = note_meta.get('view_count', 0) + 1
                self._save_metadata(metadata)
                return True
        return False
    
    def update_note(self, note_id, title=None, content=None, category=None, user_id=None):
        """Cập nhật note"""
        metadata = self._load_metadata()
        updated = False
        
        for note_meta in metadata['notes']:
            if note_meta['id'] == int(note_id):
                if title is not None:
                    note_meta['title'] = title
                    updated = True
                
                if category is not None:
                    note_meta['category'] = category
                    updated = True
                
                if content is not None:
                    # Đảm bảo thư mục tồn tại
                    os.makedirs(self.notes_dir, exist_ok=True)
                    
                    # Cập nhật file text
                    filepath = os.path.join(self.notes_dir, note_meta['filename'])
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        updated = True
                    except Exception as e:
                        raise Exception(f"Không thể cập nhật file ghi chú: {str(e)}")
                
                if updated:
                    note_meta['updated_at'] = datetime.utcnow().isoformat()
                    if user_id is not None:
                        note_meta['updated_by'] = user_id
                    self._save_metadata(metadata)
                break
        
        return updated
    
    def delete_note(self, note_id):
        """Xóa note"""
        metadata = self._load_metadata()
        for note_meta in metadata['notes']:
            if note_meta['id'] == int(note_id):
                # Xóa file text
                filepath = os.path.join(self.notes_dir, note_meta['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Xóa tất cả attachments
                for attachment in note_meta.get('attachments', []):
                    attach_path = os.path.join(self.notes_uploads_dir, attachment['filename'])
                    if os.path.exists(attach_path):
                        os.remove(attach_path)
                
                # Xóa metadata
                metadata['notes'].remove(note_meta)
                self._save_metadata(metadata)
                return True
        return False
    
    def get_total_storage_size(self):
        """Tính tổng dung lượng đã sử dụng (bytes)"""
        total_size = 0
        
        # Tính dung lượng uploads
        for root, dirs, files in os.walk(self.uploads_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        # Tính dung lượng notes
        for root, dirs, files in os.walk(self.notes_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        # Tính dung lượng docs
        for root, dirs, files in os.walk(self.docs_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        return total_size
    
    def check_storage_available(self, file_size, max_storage=2*1024*1024*1024):
        """
        Kiểm tra xem còn đủ dung lượng để upload file không
        
        Args:
            file_size: Kích thước file muốn upload (bytes)
            max_storage: Giới hạn tổng dung lượng (bytes), mặc định 2GB
        
        Returns:
            (bool, str): (True/False, message)
        """
        current_size = self.get_total_storage_size()
        
        if current_size + file_size > max_storage:
            used_mb = current_size / (1024 * 1024)
            max_mb = max_storage / (1024 * 1024)
            return False, f"Không đủ dung lượng! Đã dùng {used_mb:.1f}MB/{max_mb:.0f}MB"
        
        return True, "OK"
    
    def add_note_attachment(self, note_id, uploaded_file):
        """Thêm file đính kèm vào note"""
        import uuid
        from werkzeug.utils import secure_filename
        
        # Kiểm tra dung lượng trước khi upload
        uploaded_file.seek(0, 2)  # Seek to end
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)  # Reset to beginning
        
        can_upload, message = self.check_storage_available(file_size)
        if not can_upload:
            return False, message
        
        metadata = self._load_metadata()
        for note_meta in metadata['notes']:
            if note_meta['id'] == int(note_id):
                # Lấy phần mở rộng file
                original_filename = secure_filename(uploaded_file.filename)
                if not original_filename:
                    return False, "Tên file không hợp lệ"
                    
                file_ext = os.path.splitext(original_filename)[1]
                
                # Tạo tên file duy nhất
                unique_filename = f"{note_id}_{uuid.uuid4().hex[:8]}{file_ext}"
                filepath = os.path.join(self.notes_uploads_dir, unique_filename)
                
                # Lưu file
                uploaded_file.save(filepath)
                
                # Thêm vào metadata
                if 'attachments' not in note_meta:
                    note_meta['attachments'] = []
                
                note_meta['attachments'].append({
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'uploaded_at': datetime.utcnow().isoformat()
                })
                note_meta['updated_at'] = datetime.utcnow().isoformat()
                
                self._save_metadata(metadata)
                return True, "Upload thành công"
        return False, "Không tìm thấy ghi chú"
    
    def delete_note_attachment(self, note_id, attachment_filename):
        """Xóa file đính kèm từ note - Dù file vật lý còn hay không thì vẫn xóa attachment khỏi metadata"""
        metadata = self._load_metadata()
        for note_meta in metadata['notes']:
            if note_meta['id'] == int(note_id):
                attachments = note_meta.get('attachments', [])
                for attachment in attachments:
                    if attachment['filename'] == attachment_filename:
                        # Xóa file vật lý nếu còn
                        filepath = os.path.join(self.notes_uploads_dir, attachment_filename)
                        if os.path.exists(filepath):
                            try:
                                os.remove(filepath)
                            except Exception as e:
                                print(f"[DEBUG] ERROR khi xóa file vật lý: {e}")
                        # Xóa khỏi metadata (luôn làm)
                        attachments.remove(attachment)
                        note_meta['updated_at'] = datetime.utcnow().isoformat()
                        self._save_metadata(metadata)
                        print(f"[DEBUG] Đã xóa attachment ({attachment_filename}) khỏi metadata note {note_id}")
                        return True
        print(f"[DEBUG] Không tìm thấy note hoặc attachment: note_id={note_id}, filename={attachment_filename}")
        return False
    
    def get_note_categories(self):
        """Lấy danh sách categories của notes"""
        metadata = self._load_metadata()
        categories = set()
        for note_meta in metadata.get('notes', []):
            categories.add(note_meta.get('category', 'general'))
        return sorted(list(categories))
    
    # === DOCUMENTS METHODS ===
    def create_doc(self, title, content, category='general', user_id=None):
        """Tạo document mới"""
        doc_id = self.get_next_id('doc')
        
        # Đảm bảo thư mục tồn tại
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Lưu nội dung vào file text
        filename = f"{doc_id}.txt"
        filepath = os.path.join(self.docs_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Không thể tạo file tài liệu: {str(e)}")
        
        # Thêm metadata
        metadata = self._load_metadata()
        doc_meta = {
            'id': doc_id,
            'title': title,
            'filename': filename,
            'category': category,
            'user_id': user_id,
            'attachments': [],  # Danh sách file đính kèm
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        metadata['docs'].append(doc_meta)
        self._save_metadata(metadata)
        
        return self.get_doc(doc_id)
    
    def get_doc(self, doc_id):
        """Lấy document theo ID"""
        metadata = self._load_metadata()
        for doc_meta in metadata.get('docs', []):
            if doc_meta['id'] == int(doc_id):
                # Đọc nội dung từ file
                filepath = os.path.join(self.docs_dir, doc_meta['filename'])
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    return Document(
                        id=doc_meta['id'],
                        title=doc_meta['title'],
                        content=content,
                        category=doc_meta.get('category', 'general'),
                        user_id=doc_meta.get('user_id'),
                        attachments=doc_meta.get('attachments', []),
                        created_at=datetime.fromisoformat(doc_meta['created_at']),
                        updated_at=datetime.fromisoformat(doc_meta.get('updated_at', doc_meta['created_at']))
                    )
        return None
    
    def get_all_docs(self, category=None, search_query=None):
        """Lấy tất cả documents (có thể filter)"""
        metadata = self._load_metadata()
        docs = []
        
        for doc_meta in metadata.get('docs', []):
            # Filter theo category
            if category and category != 'all' and doc_meta.get('category') != category:
                continue
            
            # Đọc nội dung
            filepath = os.path.join(self.docs_dir, doc_meta['filename'])
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Filter theo search query
                if search_query:
                    if search_query.lower() not in doc_meta['title'].lower() and \
                       search_query.lower() not in content.lower():
                        continue
                
                doc = Document(
                    id=doc_meta['id'],
                    title=doc_meta['title'],
                    content=content,
                    category=doc_meta.get('category', 'general'),
                    user_id=doc_meta.get('user_id'),
                    attachments=doc_meta.get('attachments', []),
                    created_at=datetime.fromisoformat(doc_meta['created_at']),
                    updated_at=datetime.fromisoformat(doc_meta.get('updated_at', doc_meta['created_at']))
                )
                docs.append(doc)
        
        # Sắp xếp theo updated_at giảm dần
        docs.sort(key=lambda x: x.updated_at, reverse=True)
        return docs
    
    def update_doc(self, doc_id, title=None, content=None, category=None):
        """Cập nhật document"""
        metadata = self._load_metadata()
        updated = False
        
        for doc_meta in metadata['docs']:
            if doc_meta['id'] == int(doc_id):
                if title is not None:
                    doc_meta['title'] = title
                    updated = True
                
                if category is not None:
                    doc_meta['category'] = category
                    updated = True
                
                if content is not None:
                    # Đảm bảo thư mục tồn tại
                    os.makedirs(self.docs_dir, exist_ok=True)
                    
                    # Cập nhật file text
                    filepath = os.path.join(self.docs_dir, doc_meta['filename'])
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        updated = True
                    except Exception as e:
                        raise Exception(f"Không thể cập nhật file tài liệu: {str(e)}")
                
                if updated:
                    doc_meta['updated_at'] = datetime.utcnow().isoformat()
                    self._save_metadata(metadata)
                break
        
        return updated
    
    def delete_doc(self, doc_id):
        """Xóa document"""
        metadata = self._load_metadata()
        for doc_meta in metadata['docs']:
            if doc_meta['id'] == int(doc_id):
                # Xóa file text
                filepath = os.path.join(self.docs_dir, doc_meta['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Xóa tất cả attachments
                for attachment in doc_meta.get('attachments', []):
                    attach_path = os.path.join(self.docs_uploads_dir, attachment['filename'])
                    if os.path.exists(attach_path):
                        os.remove(attach_path)
                
                # Xóa metadata
                metadata['docs'].remove(doc_meta)
                self._save_metadata(metadata)
                return True
        return False
    
    def add_doc_attachment(self, doc_id, uploaded_file):
        """Thêm file đính kèm vào document"""
        import uuid
        from werkzeug.utils import secure_filename
        
        metadata = self._load_metadata()
        for doc_meta in metadata['docs']:
            if doc_meta['id'] == int(doc_id):
                # Lấy phần mở rộng file
                original_filename = secure_filename(uploaded_file.filename)
                if not original_filename:
                    return False
                    
                file_ext = os.path.splitext(original_filename)[1]
                
                # Tạo tên file duy nhất
                unique_filename = f"{doc_id}_{uuid.uuid4().hex[:8]}{file_ext}"
                filepath = os.path.join(self.docs_uploads_dir, unique_filename)
                
                # Lưu file
                uploaded_file.save(filepath)
                
                # Thêm vào metadata
                if 'attachments' not in doc_meta:
                    doc_meta['attachments'] = []
                
                doc_meta['attachments'].append({
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'uploaded_at': datetime.utcnow().isoformat()
                })
                doc_meta['updated_at'] = datetime.utcnow().isoformat()
                
                self._save_metadata(metadata)
                return True
        return False
    
    def delete_doc_attachment(self, doc_id, attachment_filename):
        """Xóa file đính kèm từ document"""
        metadata = self._load_metadata()
        for doc_meta in metadata['docs']:
            if doc_meta['id'] == int(doc_id):
                attachments = doc_meta.get('attachments', [])
                for attachment in attachments:
                    if attachment['filename'] == attachment_filename:
                        # Xóa file vật lý
                        filepath = os.path.join(self.docs_uploads_dir, attachment_filename)
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        
                        # Xóa khỏi metadata
                        attachments.remove(attachment)
                        doc_meta['updated_at'] = datetime.utcnow().isoformat()
                        self._save_metadata(metadata)
                        return True
        return False
    
    def get_doc_categories(self):
        """Lấy danh sách categories của documents"""
        metadata = self._load_metadata()
        categories = set()
        for doc_meta in metadata.get('docs', []):
            categories.add(doc_meta.get('category', 'general'))
        return sorted(list(categories))


class Note:
    """Note class"""
    def __init__(self, id, title, content, category='general', user_id=None, 
                 attachments=None, view_count=0, created_at=None, updated_at=None, updated_by=None):
        self.id = id
        self.title = title
        self.content = content
        self.category = category
        self.user_id = user_id
        self.attachments = attachments or []
        self.view_count = view_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.updated_by = updated_by


class Document:
    """Document class"""
    def __init__(self, id, title, content, category='general', user_id=None,
                 attachments=None, created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.content = content
        self.category = category
        self.user_id = user_id
        self.attachments = attachments or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

