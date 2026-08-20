import { useEffect, useState } from 'react';
import api from '../api/client';

export default function CommentSection({ recordId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');

  const load = async () => {
    const data = await api.getComments(recordId);
    setComments(data);
  };

  useEffect(() => { load(); }, [recordId]);

  const add = async () => {
    await api.addComment(recordId, { text: newComment });
    setNewComment('');
    load();
  };

  return (
    <div className="mt-4 border-t pt-4">
      <h4 className="font-semibold">Comments</h4>
      {comments.map(c => (
        <div key={c.id} className="text-sm text-gray-600 mt-1">
          <b>{c.user_name}</b>: {c.text}
        </div>
      ))}
      <div className="flex gap-2 mt-2">
        <input
          className="flex-1 border rounded px-2 py-1"
          value={newComment}
          onChange={e => setNewComment(e.target.value)}
        />
        <button onClick={add} className="bg-primary-600 text-white px-3 py-1 rounded">Post</button>
      </div>
    </div>
  );
}
