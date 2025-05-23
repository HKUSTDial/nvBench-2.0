% ====== Generators ======

% helpers to generate attributes based on whether they are required.
{ attribute(N,root,V) : domain(N,V) } = 1 :- root_required(N).
{ attribute((N,A),E,V): domain((N,A),V) } = 1 :- entity(N,_,E), required((N,A)).
0 { attribute((N,A),E,V): domain((N,A),V) } 1 :- entity(N,_,E), not_required((N,A)).

% maximum number of non-layered views.
#const max_views = 1.
{ entity(view,root,(v,0..max_views-1)) }.
:- { entity(view,root,_) } > max_views.
:- entity(view,root,(v,ID)), not entity(view,root,(v,ID-1)), ID > 0.

% @generator(coordinates) Each view requires coordinates.
% required((view,coordinates)).

% maximum number of additional marks for each view.
#const max_marks = 2.
{ mark_id(V,0..max_marks-1) } :- entity(view,root,V).
:- mark_id(V,ID), not mark_id(V,ID-1), ID > 0.
entity(mark,V,(V,M)) :- mark_id(V,M).

% maximum number for additional encoding channels.
#const max_encs = 4.
{ enc_id(M,0..max_encs-1) } :- entity(mark,V,M).
:- enc_id(M,ID), not enc_id(M,ID-1), ID > 0.
entity(encoding,M,(M,E)) :- enc_id(M,E).

% @generate(encoding_channel) Each encoding requires a channel.
required((encoding,channel)).
% @generator(mark_type) Each mark requires a type.
required((mark,type)).
% @generator(task) Each root requires a task.
% root_required(task).
% root_required(mark).

required((field,identifier)).

% @generator(encoding_attribute) Encoding with binning, aggregate, field or stack.
not_required((encoding,binning)).
not_required((encoding,aggregate)).
not_required((encoding,stack)).

0 { attribute((encoding,field),E,N): domain((field,name),N) } 1 :- entity(encoding,_,E).

% % generator(facet) Each specification can have at most both row and col facet.
% facet_id(0..1).
% { entity(facet,V,(fc,F)) : facet_id(F), entity(view,root,V) }.
% :- entity(facet,V,(fc,1)), not entity(facet,V,(fc,0)),facet_id(1), facet_id(0).

% required((facet,channel)).
% not_required((facet,binning)).
% { attribute((facet,field),E,N): domain((field,name),N) } = 1 :- entity(facet,_,E).

